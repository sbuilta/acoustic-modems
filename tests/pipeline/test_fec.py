"""Unit tests for forward error correction helpers."""

from __future__ import annotations

import numpy as np

import amw.pipeline.fec as fec


def bits_from_int(value: int, width: int) -> np.ndarray:
    return np.unpackbits(np.array([value], dtype=np.uint16))[-width:].astype(np.uint8)


def test_noop_codec_roundtrip() -> None:
    codec = fec.build_codec(fec.FECConfig(scheme="none"))
    original = bits_from_int(0b10101100, 8)
    encoded = codec.encode(original)
    decoded, metrics = codec.decode(encoded)
    assert np.array_equal(decoded, original)
    assert metrics["corrected_bits"] == 0
    assert metrics["uncorrectable_blocks"] == 0


def test_repetition_codec_corrects_single_symbol_error() -> None:
    codec = fec.build_codec(fec.FECConfig(scheme="repetition", repetition_factor=3))
    original = bits_from_int(0b1101, 4)
    encoded = codec.encode(original)
    # Flip one replica in the second group.
    encoded[3] ^= 1
    decoded, metrics = codec.decode(encoded)
    assert np.array_equal(decoded, original)
    assert metrics["corrected_bits"] == 1
    assert metrics["uncorrectable_blocks"] == 0


def test_hamming74_codec_corrects_single_bit_error() -> None:
    codec = fec.build_codec(fec.FECConfig(scheme="hamming74"))
    original = bits_from_int(0b101101011, 9)
    encoded = codec.encode(original)
    # Introduce a single error in the first code word.
    encoded[0] ^= 1
    decoded, metrics = codec.decode(encoded)
    assert np.array_equal(decoded[: original.size], original)
    assert metrics["corrected_bits"] == 1
    assert metrics["uncorrectable_blocks"] == 0
