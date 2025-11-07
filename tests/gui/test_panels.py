from __future__ import annotations

import pytest

from tests._qt_stub import ensure_qt_module

ensure_qt_module()

pytest.importorskip("PySide6")

from amw.gui.panels import AudioPanel, DebugPanel, ModemPanel, PayloadPanel, PipelinePanel  # noqa: E402


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


def test_debug_panel_tabs(qt_app: object) -> None:
    panel = DebugPanel()
    assert panel.tabs.count() == 4
