"""Minimal PySide6 stub for headless test environments."""

from __future__ import annotations

from types import SimpleNamespace

from amw.gui import _qt

QtWidgets = SimpleNamespace(
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

QtCore = SimpleNamespace(Qt=_qt.Qt)

__all__ = ["QtWidgets", "QtCore"]
