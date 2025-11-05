"""Data models representing pipeline artifacts and state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt


Array1D = npt.NDArray[np.float32]


class PipelineState(Enum):
    """High-level state of the pipeline execution."""

    IDLE = auto()
    BUILT = auto()
    TRANSMITTING = auto()
    RECORDING = auto()
    CONDITIONED = auto()
    DECODED = auto()


@dataclass(slots=True)
class PipelineArtifacts:
    """Holds in-memory buffers and file system artifacts created by the pipeline."""

    tx_waveform: Array1D | None = None
    rx_raw: Array1D | None = None
    rx_conditioned: Array1D | None = None
    decoded_payload: bytes | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    files: dict[str, Path] = field(default_factory=dict)

    def clear(self) -> None:
        """Reset all captured artifacts."""
        self.tx_waveform = None
        self.rx_raw = None
        self.rx_conditioned = None
        self.decoded_payload = None
        self.metadata.clear()
        self.files.clear()
