from __future__ import annotations

import numpy as np

from amw.pipeline.conditioner import ConditionHints, Conditioner


def test_conditioner_normalizes_audio() -> None:
    samples = np.array([0.0, 0.5, -1.0], dtype=np.float32)
    conditioner = Conditioner()
    result = conditioner.condition(samples, sample_rate=48000, hints=ConditionHints(target_rms_db=-9.0))
    assert np.isclose(np.max(np.abs(result.waveform)), 1.0)
    assert result.metrics["normalized"] is True


def test_conditioner_handles_edge_cases() -> None:
    conditioner = Conditioner()
    empty = np.array([], dtype=np.float32)
    result_empty = conditioner.condition(empty, sample_rate=44100)
    assert result_empty.waveform.size == 0

    zeros = np.zeros(4, dtype=np.float32)
    result_zeros = conditioner.condition(zeros, sample_rate=44100)
    assert np.array_equal(result_zeros.waveform, zeros)
