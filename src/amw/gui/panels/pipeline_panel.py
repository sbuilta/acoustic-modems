"""Pipeline control panel exposing transmit/receive actions."""

from __future__ import annotations

from enum import Enum

from .._qt import QLabel, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, QWidget


class AudioState(Enum):
    """Discrete audio activity indicators surfaced in the pipeline panel."""

    AVAILABLE = "Available"
    PLAYING = "Playing"
    ARMED = "Armed"
    RECORDING = "Recording"


class AudioStateIndicator(QWidget):
    """Compact widget that highlights the active audio state."""

    def __init__(self) -> None:
        super().__init__()
        self._labels: dict[AudioState, QLabel] = {}
        self._active_state = AudioState.AVAILABLE
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        for state in AudioState:
            label = QLabel()
            label.setObjectName(f"audio-state-{state.name.lower()}")
            self._labels[state] = label
            layout.addWidget(label)
        self.set_state(self._active_state)

    def set_state(self, state: AudioState) -> None:
        """Highlight the provided state and dim the rest."""
        self._active_state = state
        for candidate, label in self._labels.items():
            prefix = "[*]" if candidate is state else "[ ]"
            label.setText(f"{prefix} {candidate.value}")

    def current_state(self) -> AudioState:
        """Expose the active state for tests."""
        return self._active_state

    def status_text(self) -> str:
        """Return the textual representation of the active pill."""
        return self._labels[self._active_state].text()


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
        self._state_caption = QLabel("Audio state")
        self._audio_state_indicator = AudioStateIndicator()
        self._current_audio_state = AudioState.AVAILABLE
        self._build_ui()
        self.set_audio_state(self._current_audio_state)

    def set_audio_state(self, state: AudioState) -> None:
        """Update the indicator row to reflect the provided state."""
        self._current_audio_state = state
        self._audio_state_indicator.set_state(state)

    def current_audio_state(self) -> AudioState:
        """Return the last state requested by the controller."""
        return self._current_audio_state

    def audio_state_summary(self) -> str:
        """Short textual summary useful for tooltips/tests."""
        return self._audio_state_indicator.status_text()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.addWidget(self.build_button, 0, 0)
        layout.addWidget(self.tx_button, 0, 1)
        layout.addWidget(self.rx_now_button, 1, 0)
        layout.addWidget(self.rx_arm_button, 1, 1)
        layout.addWidget(self.condition_button, 2, 0)
        layout.addWidget(self.decode_button, 2, 1)
        layout.addWidget(self._state_caption, 3, 0)
        layout.addWidget(self._audio_state_indicator, 3, 1)
