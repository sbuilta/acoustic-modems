from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np

import amw.gui.controller as controller_module

from amw.gui.controller import WorkbenchController
from amw.gui.main_window import MainWindow
from amw.gui.panels.pipeline_panel import AudioState
from amw.io.audio import RecordingResult
from amw.pipeline.artifacts import PipelineArtifacts, PipelineState
from amw.plugins.contract import DecodeOutput, EncodeOutput, PluginHandle, PluginMetadata


class DummyRegistry:
    def __init__(self) -> None:
        metadata = PluginMetadata(name="Stub Modem", version="1.0.0", sample_rate=48_000, description="stub")
        defaults = {"sample_rate": 48_000, "bitrate": 100.0}

        def _encode(_: bytes, __: dict) -> EncodeOutput:
            waveform = np.zeros(8, dtype=np.float32)
            return EncodeOutput(waveform=waveform, metadata={})

        def _decode(_: np.ndarray, __: dict) -> DecodeOutput:
            return DecodeOutput(payload=b"", metrics={})

        self.handle = PluginHandle(
            metadata=metadata,
            encode=_encode,
            decode=_decode,
            schema={},
            default_params=defaults,
        )
        self._plugins = {self.handle.name: self.handle}

    def all(self) -> dict[str, PluginHandle]:
        return dict(self._plugins)

    def get(self, name: str) -> PluginHandle | None:
        return self._plugins.get(name)


class DummyAudioService:
    def list_devices(self) -> tuple[list[str], list[str]]:
        return (["Default Out"], ["Default In"])


class DummyOrchestrator:
    def __init__(self) -> None:
        self.configure_calls: list[tuple[str, dict, object]] = []
        self.build_calls = 0
        self.artifacts = PipelineArtifacts()
        self.state = PipelineState.IDLE

    def configure(self, plugin_name: str, params: dict, payload_spec: object) -> None:
        self.configure_calls.append((plugin_name, params, payload_spec))

    def build(self) -> EncodeOutput:
        self.build_calls += 1
        waveform = np.ones(4, dtype=np.float32)
        self.artifacts.tx_waveform = waveform
        return EncodeOutput(waveform=waveform, metadata={})

    def transmit(self, gain: float = 1.0) -> None:  # noqa: ARG002 - signature parity
        return

    def record(self, duration: float, use_trigger: bool = False) -> RecordingResult:  # noqa: ARG002
        samples = np.zeros(10, dtype=np.float32)
        return RecordingResult(samples=samples, sample_rate=48_000, metadata={})

    def condition(self) -> SimpleNamespace:
        return SimpleNamespace(waveform=np.zeros(2, dtype=np.float32))

    def decode(self) -> DecodeOutput:
        return DecodeOutput(payload=b"ok", metrics={})


def test_controller_populates_modems_and_devices(qt_app: object) -> None:
    window = MainWindow()
    registry = DummyRegistry()
    WorkbenchController(window, registry=registry, audio_service=DummyAudioService(), orchestrator=DummyOrchestrator())

    assert window.modem_panel.modem_selector.count() == 1
    parsed = json.loads(window.modem_panel.param_editor.toPlainText())
    assert parsed == registry.handle.default_params
    assert window.audio_panel.output_device.count() == 1
    assert window.audio_panel.input_device.count() == 1


def test_build_button_invokes_pipeline(qt_app: object) -> None:
    window = MainWindow()
    registry = DummyRegistry()
    orchestrator = DummyOrchestrator()
    WorkbenchController(window, registry=registry, audio_service=DummyAudioService(), orchestrator=orchestrator)

    window.payload_panel.text_edit.setPlainText("hello")
    window.pipeline_panel.build_button.click()

    assert orchestrator.build_calls == 1
    assert orchestrator.configure_calls, "controller should configure orchestrator before build"
    plugin_name, params, payload_spec = orchestrator.configure_calls[0]
    assert plugin_name == registry.handle.name
    assert params == registry.handle.default_params
    assert payload_spec.mode.name == "TEXT"


def test_controller_flushes_qt_events_after_audio_state_update(qt_app: object, monkeypatch: object) -> None:
    window = MainWindow()
    registry = DummyRegistry()
    controller = WorkbenchController(window, registry=registry, audio_service=DummyAudioService(), orchestrator=DummyOrchestrator())

    calls: list[int] = []

    class DummyApp:
        def processEvents(self) -> None:
            calls.append(1)

    dummy_app = DummyApp()

    def fake_instance(_: type[object]) -> DummyApp:
        return dummy_app

    monkeypatch.setattr(controller_module.QApplication, "instance", classmethod(fake_instance))

    controller._set_audio_state(AudioState.RECORDING)

    assert calls, "controller should process Qt events to refresh indicators"
