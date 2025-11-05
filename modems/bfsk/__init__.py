"""BFSK reference modem plugin with optional forward error correction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from amw.pipeline.fec import FECConfig, build_codec
from amw.plugins.contract import DecodeOutput, EncodeOutput, PluginMetadata

from .schema import load_defaults, load_schema

Array1D = npt.NDArray[np.float32]
BitArray = npt.NDArray[np.uint8]

PLUGIN_METADATA = PluginMetadata(
    name="BFSK Reference",
    version="0.2.0",
    sample_rate=48_000,
    description="Binary frequency shift keying modem with optional FEC for loopback tests.",
    author="Acoustic Modem Workbench",
    license="MIT",
)

PARAM_SCHEMA = load_schema()
DEFAULT_PARAMS = load_defaults()

_HEADER_BITS = 32


@dataclass(slots=True)
class _FECSettings:
    config: FECConfig
    interleave_depth: int


def encode(payload: bytes, params: dict[str, Any]) -> EncodeOutput:
    """Generate a BFSK waveform from the given payload."""
    config = {**DEFAULT_PARAMS, **params}
    sample_rate = int(config["sample_rate"])
    bit_rate = float(config["bitrate"])
    freq0 = float(config["freq0"])
    freq1 = float(config["freq1"])
    amplitude = float(config["amplitude"])
    preamble_bits = str(config.get("preamble_bits", "10101010"))

    fec_settings = _parse_fec_settings(config.get("fec", {}))
    codec = build_codec(fec_settings.config)

    preamble = _preamble_array(preamble_bits)
    payload_bits = _payload_bits(payload)

    if fec_settings.config.scheme == "none":
        frame_bits = payload_bits
    else:
        header = _length_header(payload_bits.size)
        frame_bits = np.concatenate([header, payload_bits]) if payload_bits.size else header

    encoded_bits = codec.encode(frame_bits)
    if fec_settings.interleave_depth > 1 and encoded_bits.size:
        encoded_bits = _interleave_bits(encoded_bits, fec_settings.interleave_depth)

    bit_stream = np.concatenate([preamble, encoded_bits]) if encoded_bits.size else preamble
    samples_per_bit = max(int(sample_rate / bit_rate), 1)
    time_axis = np.arange(samples_per_bit, dtype=np.float32) / sample_rate

    if bit_stream.size == 0:
        waveform = np.array([], dtype=np.float32)
    else:
        segments = []
        for bit in bit_stream:
            freq = freq1 if bit else freq0
            segment = amplitude * np.sin(2 * np.pi * freq * time_axis)
            segments.append(segment)
        waveform = np.concatenate(segments).astype(np.float32) if segments else np.array([], dtype=np.float32)

    metadata = {
        "bit_count": int(bit_stream.size),
        "preamble_bits": preamble_bits,
        "freq0": freq0,
        "freq1": freq1,
        "bitrate": bit_rate,
        "fec": {
            "scheme": fec_settings.config.scheme,
            "repetition_factor": fec_settings.config.repetition_factor,
            "interleave_depth": fec_settings.interleave_depth,
            "payload_bits": int(payload_bits.size),
            "encoded_bits": int(encoded_bits.size),
        },
    }
    return EncodeOutput(waveform=waveform, metadata=metadata)


def decode(waveform: Array1D, params: dict[str, Any]) -> DecodeOutput:
    """Decode the conditioned waveform using tone energy comparisons."""
    config = {**DEFAULT_PARAMS, **params}
    sample_rate = int(config["sample_rate"])
    bit_rate = float(config["bitrate"])
    freq0 = float(config["freq0"])
    freq1 = float(config["freq1"])
    preamble_bits = str(config.get("preamble_bits", "10101010"))

    fec_settings = _parse_fec_settings(config.get("fec", {}))
    codec = build_codec(fec_settings.config)

    samples_per_bit = max(int(sample_rate / bit_rate), 1)
    usable_length = (waveform.size // samples_per_bit) * samples_per_bit
    trimmed = waveform[:usable_length].reshape(-1, samples_per_bit)

    time_axis = np.arange(samples_per_bit, dtype=np.float32) / sample_rate
    carrier0 = np.sin(2 * np.pi * freq0 * time_axis)
    carrier1 = np.sin(2 * np.pi * freq1 * time_axis)

    bits = []
    for segment in trimmed:
        energy0 = float(np.dot(segment, carrier0))
        energy1 = float(np.dot(segment, carrier1))
        bits.append(1 if abs(energy1) >= abs(energy0) else 0)

    preamble_len = len(preamble_bits)
    metrics: dict[str, Any] = {
        "bit_count": len(bits),
        "preamble_bits": preamble_len,
    }

    if fec_settings.config.scheme == "none":
        data_bits = bits[preamble_len:] if preamble_len < len(bits) else []
        data_array = np.array(data_bits, dtype=np.uint8)
        payload = np.packbits(data_array).tobytes() if data_array.size else b""
        metrics["data_bits"] = len(data_bits)
        return DecodeOutput(payload=payload, metrics=metrics)

    encoded_bits = np.array(bits[preamble_len:], dtype=np.uint8)
    if fec_settings.interleave_depth > 1 and encoded_bits.size:
        encoded_bits = _deinterleave_bits(encoded_bits, fec_settings.interleave_depth)

    decoded_bits, fec_metrics = codec.decode(encoded_bits)

    if decoded_bits.size < _HEADER_BITS:
        metrics["fec"] = {**fec_metrics, "scheme": fec_settings.config.scheme, "status": "header_not_recovered"}
        return DecodeOutput(payload=b"", metrics=metrics)

    header_bits = decoded_bits[:_HEADER_BITS]
    length_bytes = np.packbits(header_bits).tobytes()
    payload_bit_length = int.from_bytes(length_bytes, byteorder="big")

    available = decoded_bits[_HEADER_BITS :]
    if available.size < payload_bit_length:
        fec_metrics["truncated_bits"] = int(payload_bit_length - available.size)
        payload_bit_length = available.size

    payload_bits = available[:payload_bit_length]
    payload = _bits_to_bytes(payload_bits)

    fec_metrics.update(
        {
            "scheme": fec_settings.config.scheme,
            "interleave_depth": fec_settings.interleave_depth,
            "payload_bits": int(payload_bit_length),
            "encoded_bits": int(encoded_bits.size),
        }
    )
    metrics["fec"] = fec_metrics
    metrics["data_bits"] = int(payload_bit_length)
    return DecodeOutput(payload=payload, metrics=metrics)


def _parse_fec_settings(raw: Any) -> _FECSettings:
    config = raw if isinstance(raw, dict) else {}
    scheme = str(config.get("scheme", "none")).lower()
    repetition_factor = int(config.get("repetition_factor", 3) or 3)
    interleave_depth = max(int(config.get("interleave_depth", 1) or 1), 1)
    fec_config = FECConfig(scheme=scheme, repetition_factor=repetition_factor)
    return _FECSettings(config=fec_config, interleave_depth=interleave_depth)


def _preamble_array(preamble_bits: str) -> BitArray:
    return np.array([1 if char == "1" else 0 for char in preamble_bits], dtype=np.uint8)


def _payload_bits(payload: bytes) -> BitArray:
    if not payload:
        return np.array([], dtype=np.uint8)
    return np.unpackbits(np.frombuffer(payload, dtype=np.uint8))


def _length_header(bit_length: int) -> BitArray:
    value = np.array(
        [
            (bit_length >> 24) & 0xFF,
            (bit_length >> 16) & 0xFF,
            (bit_length >> 8) & 0xFF,
            bit_length & 0xFF,
        ],
        dtype=np.uint8,
    )
    return np.unpackbits(value)


def _bits_to_bytes(bits: BitArray) -> bytes:
    if bits.size == 0:
        return b""
    pad = (-bits.size) % 8
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    return np.packbits(bits).tobytes()


def _interleave_bits(bits: BitArray, depth: int) -> BitArray:
    if depth <= 1 or bits.size == 0:
        return bits
    order = _interleave_indices(bits.size, depth)
    return bits[order]


def _deinterleave_bits(bits: BitArray, depth: int) -> BitArray:
    if depth <= 1 or bits.size == 0:
        return bits
    order = _interleave_indices(bits.size, depth)
    restore = np.empty_like(order)
    restore[order] = np.arange(order.size)
    return bits[restore]


def _interleave_indices(length: int, depth: int) -> np.ndarray:
    depth = max(int(depth), 1)
    if depth == 1 or length <= 1:
        return np.arange(length, dtype=np.int32)
    rows = (length + depth - 1) // depth
    order = []
    for column in range(depth):
        for row in range(rows):
            idx = row * depth + column
            if idx < length:
                order.append(idx)
    return np.array(order, dtype=np.int32)
