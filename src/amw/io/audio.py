"""Audio playback and capture services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from loguru import logger

from amw.pipeline.artifacts import Array1D

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - optional dependency under test
    sd = None


@dataclass(slots=True)
class RecordingResult:
    """Container for captured samples and metadata."""

    samples: Array1D
    sample_rate: int
    metadata: dict[str, Any] = field(default_factory=dict)


class AudioService:
    """Thin wrapper around sounddevice to keep I/O concerns isolated."""

    def __init__(self, output_device: int | None = None, input_device: int | None = None) -> None:
        self.output_device = output_device
        self.input_device = input_device

    def play(self, waveform: Array1D, sample_rate: int = 48_000, gain: float = 1.0) -> None:
        """Play a waveform to the configured output device."""
        scaled = (waveform * gain).astype(np.float32, copy=False)
        if sd is None:
            logger.warning("sounddevice not available; play() is a no-op during scaffolding.")
            logger.debug("Simulated playback of %d samples at %d Hz", scaled.size, sample_rate)
            return
        sd.play(scaled, samplerate=sample_rate, device=self.output_device, blocking=True)
        logger.debug("Playback complete")

    def record(self, duration: float, sample_rate: int, use_trigger: bool = False) -> RecordingResult:
        """Record audio for a fixed duration. Triggering is a future enhancement."""
        frames = max(int(duration * sample_rate), 0)
        logger.debug(
            "Recording request duration=%.3fs sample_rate=%d use_trigger=%s",
            duration,
            sample_rate,
            use_trigger,
        )
        if sd is None:
            logger.warning("sounddevice not available; returning silent recording.")
            samples = np.zeros(frames, dtype=np.float32)
            metadata = {"simulated": True}
        else:
            channels = 1
            recording = sd.rec(
                frames,
                samplerate=sample_rate,
                channels=channels,
                dtype="float32",
                device=self.input_device,
            )
            sd.wait()
            samples = recording.reshape(-1)
            metadata = {"channels": channels, "triggered": use_trigger}
        return RecordingResult(samples=samples, sample_rate=sample_rate, metadata=metadata)
