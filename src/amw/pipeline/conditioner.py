"""Conditioning logic to prepare recorded waveforms for decoding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .artifacts import Array1D


@dataclass(slots=True)
class ConditionHints:
    """Hints supplied by modem plugins to guide conditioning."""

    expected_duration: float | None = None
    bandpass: tuple[float, float] | None = None
    target_rms_db: float = -12.0
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class ConditionResult:
    """Container for conditioned audio and associated metrics."""

    waveform: Array1D
    metrics: dict[str, Any]


class Conditioner:
    """Applies filtering, trimming, and normalization to raw captures."""

    def condition(self, samples: Array1D, sample_rate: int, hints: ConditionHints | None = None) -> ConditionResult:
        """Return a normalized copy of the incoming waveform."""
        del sample_rate  # Placeholder until DSP routines are implemented.
        normalized = self._normalize(samples)
        return ConditionResult(waveform=normalized, metrics={"normalized": True})

    @staticmethod
    def _normalize(samples: Array1D) -> Array1D:
        if not samples.size:
            return samples
        peak = float(np.max(np.abs(samples)))
        if peak == 0:
            return samples.copy()
        return (samples / peak).astype(np.float32, copy=False)
