"""Application entry point for the Acoustic Modem Workbench GUI."""

from __future__ import annotations

from typing import Sequence

from ._qt import QApplication
from .controller import WorkbenchController
from .main_window import MainWindow


def main(argv: Sequence[str] | None = None) -> int:
    """Launch the AMW desktop application."""
    app = QApplication(list(argv) if argv is not None else [])
    window = MainWindow()
    window._controller = WorkbenchController(window)  # attribute keeps controller alive
    window.show()
    return app.exec()
