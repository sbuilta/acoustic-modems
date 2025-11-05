"""Audio device selection panel."""

from __future__ import annotations

from .._qt import QComboBox, QFormLayout, QGroupBox, QPushButton, QSpinBox, QVBoxLayout


class AudioPanel(QGroupBox):
    """Manages playback and capture device selection."""

    def __init__(self) -> None:
        super().__init__("Audio I/O")
        self.output_device = QComboBox()
        self.input_device = QComboBox()
        self.sample_rate = QSpinBox()
        self.sample_rate.setRange(8000, 192000)
        self.sample_rate.setSingleStep(1000)
        self.sample_rate.setValue(48000)
        self.refresh_button = QPushButton("Refresh Devices")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Playback device", self.output_device)
        form.addRow("Capture device", self.input_device)
        form.addRow("Sample rate (Hz)", self.sample_rate)
        layout.addLayout(form)
        layout.addWidget(self.refresh_button)

    def set_devices(self, outputs: list[str], inputs: list[str]) -> None:
        """Populate device drop-downs."""
        self.output_device.clear()
        self.output_device.addItems(outputs)
        self.input_device.clear()
        self.input_device.addItems(inputs)
