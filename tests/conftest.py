"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def qt_app() -> Generator[object, None, None]:
    """Ensure a QApplication instance exists for widget tests."""
    qt = pytest.importorskip("PySide6")
    QApplication = qt.QtWidgets.QApplication  # type: ignore[attr-defined]
    app = QApplication.instance() or QApplication([])
    yield app
