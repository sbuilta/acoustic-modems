"""Pipeline control panel exposing transmit/receive actions."""

from __future__ import annotations

from .._qt import QGridLayout, QGroupBox, QPushButton


class PipelinePanel(QGroupBox):
    """Hosts end-to-end pipeline controls."""

    def __init__(self) -> None:
        super().__init__("Pipeline")
        self.build_button = QPushButton("Build")
        self.tx_button = QPushButton("Transmit")
        self.rx_now_button = QPushButton("Record Now")
        self.rx_arm_button = QPushButton("Arm Trigger")
        self.condition_button = QPushButton("Condition")
        self.decode_button = QPushButton("Decode")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.addWidget(self.build_button, 0, 0)
        layout.addWidget(self.tx_button, 0, 1)
        layout.addWidget(self.rx_now_button, 1, 0)
        layout.addWidget(self.rx_arm_button, 1, 1)
        layout.addWidget(self.condition_button, 2, 0)
        layout.addWidget(self.decode_button, 2, 1)
