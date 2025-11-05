from __future__ import annotations

from amw.gui._qt import QSplitter
from amw.gui.main_window import MainWindow


def test_main_window_structure() -> None:
    window = MainWindow()
    splitter = window.centralWidget()
    assert isinstance(splitter, QSplitter)
    if hasattr(splitter, "_widgets"):
        assert len(splitter._widgets) == 2  # type: ignore[attr-defined]
