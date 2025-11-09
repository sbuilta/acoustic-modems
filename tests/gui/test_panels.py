from __future__ import annotations

import numpy as np
import pytest

from tests._qt_stub import ensure_qt_module

ensure_qt_module()

pytest.importorskip("PySide6")

from amw.gui.panels import AudioPanel, DebugPanel, ModemPanel, PayloadPanel  # noqa: E402
from amw.gui.panels.pipeline_panel import AudioState, PipelinePanel  # noqa: E402


def test_modem_panel_defaults(qt_app: object) -> None:
    panel = ModemPanel()
    assert panel.modem_selector.count() == 0


def test_payload_panel_toggle_updates_visibility(qt_app: object) -> None:
    panel = PayloadPanel()
    panel.file_radio.click()
    assert panel.file_path_edit.isVisible()


def test_audio_panel_defaults(qt_app: object) -> None:
    panel = AudioPanel()
    assert panel.sample_rate.value() == 48000


def test_pipeline_panel_buttons(qt_app: object) -> None:
    panel = PipelinePanel()
    assert panel.build_button.text() == "Build"
    assert panel.stop_button.text() == "Stop"
    assert panel.save_payload_button.text().startswith("Save")


def test_pipeline_panel_audio_state_indicator(qt_app: object) -> None:
    panel = PipelinePanel()
    assert panel.current_audio_state() == AudioState.AVAILABLE
    panel.set_audio_state(AudioState.PLAYING)
    assert panel.current_audio_state() == AudioState.PLAYING
    assert panel.audio_state_summary().startswith("[*] Playing")


def test_debug_panel_tabs(qt_app: object) -> None:
    panel = DebugPanel()
    assert panel.tabs.count() == 4


def test_debug_panel_updates_constellation_status(qt_app: object) -> None:
    panel = DebugPanel()
    samples = np.linspace(-1.0, 1.0, num=32, dtype=np.float32)
    panel.update_constellation(samples, 48_000)
    assert "Showing" in panel.constellation.status_text()


def test_metrics_view_tracks_status_and_tx_rx(qt_app: object) -> None:
    panel = DebugPanel()
    panel.log_status("info", "Build ready")
    panel.record_transmit(1024, 48_000)
    panel.record_receive(2048, 48_000, triggered=True, metadata={"channels": 1})
    assert "Build ready" in panel.metrics.status_text()
    assert "1 event" in panel.metrics.tx_summary()
    assert "triggered" in panel.metrics.rx_summary()


def test_metrics_view_tracks_decode_attempts(qt_app: object) -> None:
    panel = DebugPanel()
    panel.record_decode_attempt(success=True, payload_bytes=8, metrics={"ber": 0.1})
    assert "1 attempt" in panel.metrics.decode_summary()
    assert "ber" in panel.metrics.decode_metrics_text()
    panel.record_decode_attempt(success=False, error="CRC mismatch")
    assert "failure" in panel.metrics.decode_summary()
    assert "CRC mismatch" in panel.metrics.decode_metrics_text()
