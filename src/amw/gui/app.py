"""Application entry point for the Acoustic Modem Workbench GUI."""

from __future__ import annotations

from typing import Sequence

from .main_window import MainWindow
from ._qt import QApplication


def main(argv: Sequence[str] | None = None) -> int:
    """Launch the AMW desktop application."""
    app = QApplication(list(argv) if argv is not None else [])
    window = MainWindow()
    window.show()
    return app.exec()
