"""Qt import helpers with light-weight fallbacks for headless testing."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Sequence
from typing import Any

_TRUTHY = {"1", "true", "yes", "on"}
_use_stub = (os.getenv("AMW_FORCE_QT_STUBS") or "").lower() in _TRUTHY

if not _use_stub:
    try:  # pragma: no cover - exercised implicitly when Qt is available
        from PySide6.QtCore import Qt  # type: ignore
        from PySide6.QtWidgets import (  # type: ignore
            QApplication,
            QFileDialog,
            QButtonGroup,
            QCheckBox,
            QComboBox,
            QFormLayout,
            QGridLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QPushButton,
            QRadioButton,
            QSpinBox,
            QSplitter,
            QTabWidget,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except Exception:  # pragma: no cover - used during headless tests
        _use_stub = True

if _use_stub:

    class _Signal:
        def __init__(self) -> None:
            self._callbacks: list[Callable[..., object]] = []

        def connect(self, callback: Callable[..., object]) -> None:
            self._callbacks.append(callback)

        def emit(self, *args: object, **kwargs: object) -> None:
            for callback in list(self._callbacks):
                try:
                    callback(*args, **kwargs)
                except TypeError:
                    callback()

    class QWidget:
        def __init__(self) -> None:
            self._layout: object | None = None
            self._visible = True
            self._object_name = ""
            self._enabled = True

        def setLayout(self, layout: object | None) -> None:
            self._layout = layout

        def layout(self) -> object | None:
            return self._layout

        def setVisible(self, visible: bool) -> None:
            self._visible = visible

        def isVisible(self) -> bool:
            return self._visible

        def setEnabled(self, enabled: bool) -> None:
            self._enabled = enabled

        def isEnabled(self) -> bool:
            return self._enabled

        def setObjectName(self, name: str) -> None:
            self._object_name = name

        def objectName(self) -> str:
            return self._object_name

    class QGroupBox(QWidget):
        def __init__(self, title: str = "") -> None:
            super().__init__()
            self._title = title

        def title(self) -> str:
            return self._title

    class QPushButton(QWidget):
        def __init__(self, text: str = "") -> None:
            super().__init__()
            self._text = text
            self.clicked = _Signal()

        def text(self) -> str:
            return self._text

        def setText(self, text: str) -> None:
            self._text = text

        def click(self) -> None:
            self.clicked.emit()

    class QComboBox(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._items: list[str] = []
            self._current_index = -1
            self.currentIndexChanged = _Signal()

        def addItem(self, item: str) -> None:
            self._items.append(str(item))
            if self._current_index == -1:
                self._set_index(0)

        def addItems(self, items: Iterable[str]) -> None:
            for item in items:
                self.addItem(str(item))

        def clear(self) -> None:
            previous = self._current_index
            self._items.clear()
            self._current_index = -1
            if previous != -1:
                self.currentIndexChanged.emit(-1)

        def count(self) -> int:
            return len(self._items)

        def currentText(self) -> str:
            if 0 <= self._current_index < len(self._items):
                return self._items[self._current_index]
            return ""

        def currentIndex(self) -> int:
            return self._current_index

        def setCurrentIndex(self, index: int) -> None:
            self._set_index(index)

        def _set_index(self, index: int) -> None:
            if not self._items:
                index = -1
            else:
                index = max(0, min(index, len(self._items) - 1))
            if index == self._current_index:
                return
            self._current_index = index
            self.currentIndexChanged.emit(index)


    class QSpinBox(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._value = 0
            self._minimum = 0
            self._maximum = 0

        def setRange(self, minimum: int, maximum: int) -> None:
            self._minimum = minimum
            self._maximum = maximum

        def setSingleStep(self, _: int) -> None:
            return

        def setValue(self, value: int) -> None:
            value = max(self._minimum, min(self._maximum, value))
            self._value = value

        def value(self) -> int:
            return self._value

    class _CheckableWidget(QWidget):
        def __init__(self, text: str = "") -> None:
            super().__init__()
            self._text = text
            self._checked = False
            self.clicked = _Signal()

        def text(self) -> str:
            return self._text

        def setChecked(self, checked: bool) -> None:
            self._checked = checked

        def isChecked(self) -> bool:
            return self._checked

        def click(self) -> None:
            self.setChecked(True)
            self.clicked.emit()

    class QRadioButton(_CheckableWidget):
        pass

    class QCheckBox(_CheckableWidget):
        pass

    class QLineEdit(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._text = ""
            self.textChanged = _Signal()
            self._placeholder = ""

        def setPlaceholderText(self, text: str) -> None:
            self._placeholder = text

        def setText(self, text: str) -> None:
            self._text = text
            self.textChanged.emit(text)

        def text(self) -> str:
            return self._text

    class QTextEdit(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._text = ""
            self.textChanged = _Signal()

        def setPlainText(self, text: str) -> None:
            self._text = text
            self.textChanged.emit()

        def toPlainText(self) -> str:
            return self._text

    class QLabel(QWidget):
        def __init__(self, text: str = "") -> None:
            super().__init__()
            self._text = text
            self._word_wrap = False

        def setText(self, text: str) -> None:
            self._text = text

        def text(self) -> str:
            return self._text

        def setWordWrap(self, enabled: bool) -> None:
            self._word_wrap = enabled

    class QButtonGroup:
        def __init__(self, _: QWidget | None = None) -> None:
            self._buttons: list[_CheckableWidget] = []
            self.buttonClicked = _Signal()

        def addButton(self, button: _CheckableWidget) -> None:
            self._buttons.append(button)
            button.clicked.connect(lambda b=button: self._handle_click(b))

        def _handle_click(self, button: _CheckableWidget) -> None:
            for other in self._buttons:
                other.setChecked(other is button)
            self.buttonClicked.emit(button)

    class _BaseLayout:
        def __init__(self, parent: QWidget | None = None) -> None:
            self._items: list[tuple[str, object]] = []
            self._parent = parent

        def addWidget(self, widget: QWidget) -> None:
            self._items.append(("widget", widget))

        def addLayout(self, layout: _BaseLayout) -> None:
            self._items.append(("layout", layout))

        def addStretch(self, stretch: int) -> None:
            self._items.append(("stretch", stretch))

    class QVBoxLayout(_BaseLayout):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)

        def setContentsMargins(self, *args: int) -> None:
            return

        def setSpacing(self, _: int) -> None:
            return

    class QHBoxLayout(_BaseLayout):
        pass

    class QFormLayout(_BaseLayout):
        def addRow(self, label: str, widget: QWidget) -> None:
            self._items.append(("row", label, widget))

    class QGridLayout(_BaseLayout):
        def addWidget(self, widget: QWidget, row: int, column: int) -> None:
            self._items.append(("grid", widget, row, column))

    class QTabWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._tabs: list[tuple[QWidget, str]] = []

        def addTab(self, widget: QWidget, title: str) -> int:
            self._tabs.append((widget, title))
            return len(self._tabs) - 1

        def count(self) -> int:
            return len(self._tabs)

    class QSplitter(QWidget):
        def __init__(self, _: int) -> None:
            super().__init__()
            self._widgets: list[QWidget] = []
            self._stretch: dict[int, int] = {}

        def addWidget(self, widget: QWidget) -> None:
            self._widgets.append(widget)

        def setStretchFactor(self, index: int, factor: int) -> None:
            self._stretch[index] = factor

    class QMainWindow(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._central_widget: QWidget | None = None
            self._title = ""
            self._size = (0, 0)

        def setWindowTitle(self, title: str) -> None:
            self._title = title

        def resize(self, width: int, height: int) -> None:
            self._size = (width, height)

        def setCentralWidget(self, widget: QWidget) -> None:
            self._central_widget = widget

        def centralWidget(self) -> QWidget | None:
            return self._central_widget

        def show(self) -> None:
            return

    class QApplication:
        _instance: QApplication | None = None

        def __init__(self, argv: Sequence[str]) -> None:
            self.argv = list(argv)
            type(self)._instance = self

        def processEvents(self) -> None:
            return

        def exec(self) -> int:  # noqa: A003 - match Qt API
            return 0

        @classmethod
        def instance(cls) -> QApplication | None:
            return cls._instance

    class QFileDialog:
        @staticmethod
        def getOpenFileName(*_: object, **__: object) -> tuple[str, str]:
            return "", ""

        @staticmethod
        def getSaveFileName(*_: object, **__: object) -> tuple[str, str]:
            return "", ""

    class Qt:
        class Orientation:
            Horizontal = 0
            Vertical = 1

if _use_stub:
    __all__ = [
        "QApplication",
        "QButtonGroup",
        "QCheckBox",
        "QComboBox",
        "QFormLayout",
        "QGridLayout",
        "QGroupBox",
        "QHBoxLayout",
        "QLabel",
        "QLineEdit",
        "QMainWindow",
        "QPushButton",
        "QRadioButton",
        "QSpinBox",
        "QSplitter",
        "QTabWidget",
        "QTextEdit",
        "QVBoxLayout",
        "QWidget",
        "QFileDialog",
        "Qt",
    ]
else:
    __all__ = [
        "QApplication",
        "QButtonGroup",
        "QCheckBox",
        "QComboBox",
        "QFormLayout",
        "QGridLayout",
        "QGroupBox",
        "QHBoxLayout",
        "QLabel",
        "QLineEdit",
        "QMainWindow",
        "QPushButton",
        "QRadioButton",
        "QSpinBox",
        "QSplitter",
        "QTabWidget",
        "QTextEdit",
        "QVBoxLayout",
        "QWidget",
        "QFileDialog",
        "Qt",
    ]
