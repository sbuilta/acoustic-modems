"""Debug visualization panel for captured and decoded artifacts."""

from __future__ import annotations

from .._qt import QLabel, QTabWidget, QVBoxLayout, QWidget


class DebugPanel(QWidget):
    """Contains tabs for waveform, spectrogram, constellation, and metrics."""

    def __init__(self) -> None:
        super().__init__()
        self.tabs = QTabWidget()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs.addTab(self._placeholder("Waveform view coming soon"), "Waveform")
        self.tabs.addTab(self._placeholder("Spectrogram view coming soon"), "Spectrogram")
        self.tabs.addTab(self._placeholder("Constellation view coming soon"), "Constellation")
        self.tabs.addTab(self._placeholder("Metrics view coming soon"), "Metrics")

        layout.addWidget(self.tabs)

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        widget = QWidget()
        placeholder = QLabel(text)
        placeholder.setObjectName("placeholder")
        placeholder.setWordWrap(True)
        child_layout = QVBoxLayout(widget)
        child_layout.addWidget(placeholder)
        child_layout.addStretch(1)
        return widget
