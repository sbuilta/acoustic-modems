"""Forward error correction helpers shared across modem implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple

import numpy as np
import numpy.typing as npt

BitArray = npt.NDArray[np.uint8]


class FECCodec(Protocol):
    """Interface for concrete FEC codecs."""

    def encode(self, bits: BitArray) -> BitArray:
        ...

    def decode(self, bits: BitArray) -> Tuple[BitArray, dict[str, int]]:
        ...


@dataclass(slots=True)
class FECConfig:
    """Declarative configuration for FEC behaviour."""

    scheme: str = "none"
    repetition_factor: int = 3


def build_codec(config: FECConfig) -> FECCodec:
    """Factory for concrete FEC codecs."""
    scheme = config.scheme.lower()
    if scheme == "none":
        return _NoOpCodec()
    if scheme == "repetition":
        return _RepetitionCodec(config.repetition_factor)
    if scheme == "hamming74":
        return _Hamming74Codec()
    raise ValueError(f"Unsupported FEC scheme '{config.scheme}'")


class _NoOpCodec:
    """Passthrough codec used when FEC is disabled."""

    def encode(self, bits: BitArray) -> BitArray:
        return bits

    def decode(self, bits: BitArray) -> Tuple[BitArray, dict[str, int]]:
        return bits, {"corrected_bits": 0, "uncorrectable_blocks": 0}


class _RepetitionCodec:
    """Encode bits by repeating each symbol and decode via majority vote."""

    def __init__(self, factor: int) -> None:
        if factor < 1:
            raise ValueError("Repetition factor must be >= 1.")
        if factor % 2 == 0:
            raise ValueError("Repetition factor must be odd to allow majority voting.")
        self._factor = factor

    def encode(self, bits: BitArray) -> BitArray:
        if bits.size == 0:
            return bits
        return np.repeat(bits, self._factor).astype(np.uint8)

    def decode(self, bits: BitArray) -> Tuple[BitArray, dict[str, int]]:
        if bits.size == 0:
            return bits, {"corrected_bits": 0, "uncorrectable_blocks": 0}

        usable = (bits.size // self._factor) * self._factor
        trimmed = bits[:usable].reshape(-1, self._factor)
        ones = trimmed.sum(axis=1)
        majority = (ones > (self._factor // 2)).astype(np.uint8)
        corrected = np.abs(trimmed - majority[:, None]).sum()
        return majority, {
            "corrected_bits": int(corrected),
            "uncorrectable_blocks": 0,
            "discarded_symbols": int(bits.size - usable),
        }


class _Hamming74Codec:
    """(7,4) Hamming block code with single-bit error correction."""

    _generator = np.array(
        [
            [1, 1, 0, 1],
            [1, 0, 1, 1],
            [1, 0, 0, 0],
            [0, 1, 1, 1],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ],
        dtype=np.uint8,
    )

    _parity_check = np.array(
        [
            [1, 0, 1, 0, 1, 0, 1],
            [0, 1, 1, 0, 0, 1, 1],
            [0, 0, 0, 1, 1, 1, 1],
        ],
        dtype=np.uint8,
    )

    def encode(self, bits: BitArray) -> BitArray:
        if bits.size == 0:
            return bits
        pad = (-bits.size) % 4
        if pad:
            bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
        data = bits.reshape(-1, 4).T
        codewords = (self._generator @ data) % 2
        return codewords.T.reshape(-1).astype(np.uint8)

    def decode(self, bits: BitArray) -> Tuple[BitArray, dict[str, int]]:
        if bits.size == 0:
            return bits, {"corrected_bits": 0, "uncorrectable_blocks": 0, "discarded_symbols": 0}

        usable = (bits.size // 7) * 7
        trimmed = bits[:usable].reshape(-1, 7)
        syndromes = (trimmed @ self._parity_check.T) % 2
        syndrome_indices = syndromes.dot(1 << np.arange(3))

        corrected_blocks = 0
        uncorrectable = 0

        corrected = trimmed.copy()
        for idx, syndrome in enumerate(syndrome_indices):
            if syndrome == 0:
                continue
            if 1 <= syndrome <= 7:
                bit_index = syndrome - 1
                corrected[idx, bit_index] ^= 1
                corrected_blocks += 1
            else:
                uncorrectable += 1

        data = corrected[:, [2, 4, 5, 6]].reshape(-1).astype(np.uint8)
        return data, {
            "corrected_bits": int(corrected_blocks),
            "uncorrectable_blocks": int(uncorrectable),
            "discarded_symbols": int(bits.size - usable),
        }
