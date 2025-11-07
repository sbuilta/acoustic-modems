"""Utilities for providing a PySide6 stub in headless environments."""

from __future__ import annotations

import os
import sys
from types import ModuleType, SimpleNamespace

_TRUTHY = {"1", "true", "yes", "on"}


def ensure_qt_module() -> None:
    """Install the lightweight PySide6 shim if the real bindings are unavailable."""
    force_stub = (os.getenv("AMW_FORCE_QT_STUBS") or "").lower() in _TRUTHY

    if force_stub:
        sys.modules.pop("PySide6", None)
    elif "PySide6" in sys.modules:
        return

    if not force_stub:
        try:
            import PySide6  # noqa: F401  # pragma: no cover - import side effect only
        except ModuleNotFoundError:
            pass
        else:
            return

    from amw.gui import _qt

    stub = ModuleType("PySide6")
    stub.QtWidgets = SimpleNamespace(
        QApplication=_qt.QApplication,
        QButtonGroup=_qt.QButtonGroup,
        QCheckBox=_qt.QCheckBox,
        QComboBox=_qt.QComboBox,
        QFormLayout=_qt.QFormLayout,
        QGridLayout=_qt.QGridLayout,
        QGroupBox=_qt.QGroupBox,
        QHBoxLayout=_qt.QHBoxLayout,
        QLabel=_qt.QLabel,
        QLineEdit=_qt.QLineEdit,
        QMainWindow=_qt.QMainWindow,
        QPushButton=_qt.QPushButton,
        QRadioButton=_qt.QRadioButton,
        QSpinBox=_qt.QSpinBox,
        QSplitter=_qt.QSplitter,
        QTabWidget=_qt.QTabWidget,
        QTextEdit=_qt.QTextEdit,
        QVBoxLayout=_qt.QVBoxLayout,
        QWidget=_qt.QWidget,
        QFileDialog=_qt.QFileDialog,
    )
    stub.QtCore = SimpleNamespace(Qt=_qt.Qt)
    sys.modules["PySide6"] = stub
