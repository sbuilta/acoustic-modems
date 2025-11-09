"""Regression tests for BFSK modem FEC integration."""

from __future__ import annotations

import numpy as np

from modems import bfsk


def test_interleave_roundtrip() -> None:
    bits = np.array([0, 1, 1, 0, 1, 0, 0], dtype=np.uint8)
    depth = 3
    interleaved = bfsk._interleave_bits(bits, depth)  # type: ignore[attr-defined]
    restored = bfsk._deinterleave_bits(interleaved, depth)  # type: ignore[attr-defined]
    assert np.array_equal(restored, bits)


def test_bfsk_hamming_roundtrip() -> None:
    params = {
        **bfsk.DEFAULT_PARAMS,
        "fec": {
            "scheme": "hamming74",
            "interleave_depth": 4,
        },
    }
    payload = b"acoustic fec"
    encode_output = bfsk.encode(payload, params)
    decode_output = bfsk.decode(encode_output.waveform, params)
    assert decode_output.payload == payload
    assert decode_output.metrics["fec"]["scheme"] == "hamming74"


def test_bfsk_decode_survives_leading_silence_and_noise() -> None:
    params = dict(bfsk.DEFAULT_PARAMS)
    payload = b"live acoustic payload"
    encode_output = bfsk.encode(payload, params)

    sample_rate = int(params["sample_rate"])
    silence = np.zeros(sample_rate // 10, dtype=np.float32)
    rng = np.random.default_rng(42)
    noise = rng.normal(scale=0.02, size=encode_output.waveform.size).astype(np.float32)
    attenuated = 0.3 * encode_output.waveform + noise
    channel = np.concatenate([silence, attenuated, silence])

    decode_output = bfsk.decode(channel, params)
    assert decode_output.payload == payload
    assert decode_output.metrics["status"] == "ok"


def test_bfsk_decode_handles_sampling_drift() -> None:
    params = dict(bfsk.DEFAULT_PARAMS)
    payload = b"timing drift payload"
    encode_output = bfsk.encode(payload, params)

    stretched = _time_stretch(encode_output.waveform, factor=1.015)
    silence = np.zeros(2000, dtype=np.float32)
    channel = np.concatenate([silence, stretched, silence])

    decode_output = bfsk.decode(channel, params)
    assert decode_output.payload == payload
    assert decode_output.metrics["status"] == "ok"


def _time_stretch(signal: np.ndarray, factor: float) -> np.ndarray:
    if factor <= 0:
        raise ValueError("factor must be positive")
    if signal.size == 0:
        return signal
    original = np.arange(signal.size, dtype=np.float32)
    new_length = max(1, int(round(signal.size * factor)))
    sample_points = np.linspace(0, signal.size - 1, new_length, dtype=np.float32)
    stretched = np.interp(sample_points, original, signal.astype(np.float64))
    return stretched.astype(np.float32)
