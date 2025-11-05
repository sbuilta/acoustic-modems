"""BFSK reference modem plugin."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from amw.plugins.contract import DecodeOutput, EncodeOutput, PluginMetadata

from .schema import load_defaults, load_schema

Array1D = npt.NDArray[np.float32]
BitArray = npt.NDArray[np.uint8]

PLUGIN_METADATA = PluginMetadata(
    name="BFSK Reference",
    version="0.1.0",
    sample_rate=48_000,
    description="Binary frequency shift keying modem for baseline loopback tests.",
    author="Acoustic Modem Workbench",
    license="MIT",
)

PARAM_SCHEMA = load_schema()
DEFAULT_PARAMS = load_defaults()


def encode(payload: bytes, params: dict[str, Any]) -> EncodeOutput:
    """Generate a BFSK waveform from the given payload."""
    config = {**DEFAULT_PARAMS, **params}
    sample_rate = int(config["sample_rate"])
    bit_rate = float(config["bitrate"])
    freq0 = float(config["freq0"])
    freq1 = float(config["freq1"])
    amplitude = float(config["amplitude"])
    preamble_bits = str(config.get("preamble_bits", "10101010"))

    bit_stream = _bits_from_payload(payload, preamble_bits)
    samples_per_bit = max(int(sample_rate / bit_rate), 1)
    time_axis = np.arange(samples_per_bit, dtype=np.float32) / sample_rate

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
    }
    return EncodeOutput(waveform=waveform, metadata=metadata)


def decode(waveform: Array1D, params: dict[str, Any]) -> DecodeOutput:
    """Naïve BFSK decoder that selects the dominant tone per symbol window."""
    config = {**DEFAULT_PARAMS, **params}
    sample_rate = int(config["sample_rate"])
    bit_rate = float(config["bitrate"])
    freq0 = float(config["freq0"])
    freq1 = float(config["freq1"])
    preamble_bits = str(config.get("preamble_bits", "10101010"))

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
    data_bits = bits[preamble_len:] if preamble_len < len(bits) else []
    data_array = np.array(data_bits, dtype=np.uint8)
    payload = np.packbits(data_array).tobytes() if data_array.size else b""

    metrics = {
        "bit_count": len(bits),
        "data_bits": len(data_bits),
        "preamble_bits": preamble_len,
    }
    return DecodeOutput(payload=payload, metrics=metrics)


def _bits_from_payload(payload: bytes, preamble_bits: str) -> BitArray:
    preamble = np.array([1 if char == "1" else 0 for char in preamble_bits], dtype=np.uint8)
    if payload:
        payload_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
        return np.concatenate([preamble, payload_bits])
    return preamble
