"""GUI controller wiring panels to the modem pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from amw.gui.main_window import MainWindow
from amw.io.audio import AudioService
from amw.io.payload import PayloadBuilder, PayloadSpec, PayloadType
from amw.pipeline.conditioner import Conditioner
from amw.pipeline.orchestrator import PipelineOrchestrator
from amw.plugins.contract import PluginHandle
from amw.plugins.registry import PluginRegistry


class WorkbenchController:
    """Binds the Qt panels to backend services and orchestrates user actions."""

    def __init__(
        self,
        window: MainWindow,
        *,
        registry: PluginRegistry | None = None,
        audio_service: AudioService | None = None,
        conditioner: Conditioner | None = None,
        payload_builder: PayloadBuilder | None = None,
        orchestrator: PipelineOrchestrator | None = None,
    ) -> None:
        self.window = window
        self._registry = registry or PluginRegistry()
        self._audio = audio_service or AudioService()
        self._conditioner = conditioner or Conditioner()
        self._payload_builder = payload_builder or PayloadBuilder()
        self._orchestrator = orchestrator or PipelineOrchestrator(
            self._registry,
            self._audio,
            conditioner=self._conditioner,
            payload_builder=self._payload_builder,
        )
        self._plugins: dict[str, PluginHandle] = {}
        self._current_plugin: PluginHandle | None = None
        self._record_duration_s = 3.0
        self._initialize_ui()

    def _initialize_ui(self) -> None:
        panels = self.window
        panels.modem_panel.modem_selector.currentIndexChanged.connect(self._on_modem_selected)
        panels.audio_panel.refresh_button.clicked.connect(self._refresh_audio_devices)

        pipeline = panels.pipeline_panel
        pipeline.build_button.clicked.connect(self._handle_build)
        pipeline.tx_button.clicked.connect(self._handle_transmit)
        pipeline.rx_now_button.clicked.connect(lambda: self._handle_record(use_trigger=False))
        pipeline.rx_arm_button.clicked.connect(lambda: self._handle_record(use_trigger=True))
        pipeline.condition_button.clicked.connect(self._handle_condition)
        pipeline.decode_button.clicked.connect(self._handle_decode)

        self._refresh_audio_devices()
        self._load_plugins()

    def _load_plugins(self) -> None:
        self._plugins = self._registry.all()
        names = sorted(self._plugins.keys())
        self.window.modem_panel.set_available_modems(names)
        if names:
            # Trigger selection handler for the first modem.
            self._on_modem_selected(0)
        else:
            self.window.modem_panel.set_metadata(description="No modem plugins found. Verify the 'modems/' folder.")
            logger.warning("No modem plugins discovered.")

    def _on_modem_selected(self, _: Any) -> None:
        name = self.window.modem_panel.selected_modem()
        if not name:
            self._current_plugin = None
            self.window.modem_panel.set_metadata(description="Select a modem to view details.")
            self.window.modem_panel.set_params({})
            return

        plugin = self._plugins.get(name)
        if plugin is None:
            logger.error("Modem '%s' not found in registry.", name)
            self.window.modem_panel.set_metadata(description="Unknown modem selection.")
            return

        self._current_plugin = plugin
        self.window.modem_panel.set_metadata(
            description=plugin.metadata.description,
            sample_rate=plugin.sample_rate,
            version=plugin.metadata.version,
        )
        self.window.modem_panel.set_params(plugin.default_params)
        self.window.audio_panel.sample_rate.setValue(plugin.sample_rate)
        logger.info("Selected modem '%s'", plugin.name)

    def _handle_build(self) -> None:
        plugin = self._require_plugin()
        if plugin is None:
            return

        try:
            params = self.window.modem_panel.current_params()
        except ValueError as exc:
            self._notify_error(str(exc))
            return

        try:
            payload_spec = self._build_payload_spec()
        except (ValueError, FileNotFoundError) as exc:
            self._notify_error(str(exc))
            return

        try:
            self._orchestrator.configure(plugin.name, params, payload_spec)
            result = self._orchestrator.build()
        except Exception as exc:
            logger.exception("Pipeline build failed: %s", exc)
            self._notify_error(f"Build failed: {exc}")
            return

        self._notify_info(f"Build complete ({result.waveform.size} samples)")

    def _handle_transmit(self) -> None:
        try:
            self._orchestrator.transmit()
        except Exception as exc:
            logger.exception("Transmit failed: %s", exc)
            self._notify_error(f"Transmit failed: {exc}")
            return
        self._notify_info("Transmit complete")

    def _handle_record(self, *, use_trigger: bool) -> None:
        try:
            result = self._orchestrator.record(duration=self._record_duration_s, use_trigger=use_trigger)
        except Exception as exc:
            logger.exception("Record failed: %s", exc)
            self._notify_error(f"Record failed: {exc}")
            return
        self.window.debug_panel.update_constellation(result.samples, result.sample_rate)
        trigger_msg = " (trigger)" if use_trigger else ""
        self._notify_info(f"Recorded {result.samples.size} samples{trigger_msg}")

    def _handle_condition(self) -> None:
        try:
            conditioned = self._orchestrator.condition()
        except Exception as exc:
            logger.exception("Conditioning failed: %s", exc)
            self._notify_error(f"Conditioning failed: {exc}")
            return
        self._notify_info(f"Conditioned waveform of length {conditioned.waveform.size}")

    def _handle_decode(self) -> None:
        try:
            result = self._orchestrator.decode()
        except Exception as exc:
            logger.exception("Decode failed: %s", exc)
            self._notify_error(f"Decode failed: {exc}")
            return
        self._notify_info(f"Decoded payload ({len(result.payload)} bytes)")

    def _refresh_audio_devices(self) -> None:
        outputs, inputs = self._audio.list_devices()
        self.window.audio_panel.set_devices(outputs, inputs)

    def _build_payload_spec(self) -> PayloadSpec:
        panel = self.window.payload_panel
        crc_enabled = panel.crc_checkbox.isChecked()
        if panel.text_radio.isChecked():
            return PayloadSpec(mode=PayloadType.TEXT, text=panel.text_edit.toPlainText(), crc=crc_enabled)

        file_path = panel.file_path_edit.text().strip()
        if not file_path:
            raise ValueError("Select a payload file before building.")
        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Payload file '{path}' not found.")
        return PayloadSpec(mode=PayloadType.FILE, file_path=path, crc=crc_enabled)

    def _require_plugin(self) -> PluginHandle | None:
        if self._current_plugin is None:
            self._notify_error("Select a modem before running the pipeline.")
            return None
        return self._current_plugin

    def _notify_info(self, message: str) -> None:
        logger.info(message)

    def _notify_error(self, message: str) -> None:
        logger.error(message)
