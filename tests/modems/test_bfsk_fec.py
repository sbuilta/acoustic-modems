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
