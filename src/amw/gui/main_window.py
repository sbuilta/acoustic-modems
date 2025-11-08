"""Main window layout for the Acoustic Modem Workbench GUI."""

from __future__ import annotations

from ._qt import QMainWindow, QSplitter, QVBoxLayout, QWidget, Qt
from .panels import AudioPanel, DebugPanel, ModemPanel, PayloadPanel, PipelinePanel


class MainWindow(QMainWindow):
    """Primary workspace window hosting control panels and debug views."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Acoustic Modem Workbench")
        self.resize(1200, 800)
        self._setup_ui()

    def _setup_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(12, 12, 12, 12)
        control_layout.setSpacing(12)

        self.modem_panel = ModemPanel()
        self.payload_panel = PayloadPanel()
        self.audio_panel = AudioPanel()
        self.pipeline_panel = PipelinePanel()
        self.debug_panel = DebugPanel()

        control_layout.addWidget(self.modem_panel)
        control_layout.addWidget(self.payload_panel)
        control_layout.addWidget(self.audio_panel)
        control_layout.addWidget(self.pipeline_panel)
        control_layout.addStretch(1)

        splitter.addWidget(control_widget)
        splitter.addWidget(self.debug_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)
