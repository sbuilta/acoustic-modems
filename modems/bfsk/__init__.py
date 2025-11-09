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
_SYNC_TIMING_PCT = 0.02  # +/- timing search window
_SYNC_TIMING_STEPS = 5
_SYNC_MIN_SCORE = 0.3
_SYNC_MIN_WINDOW = 8
_AGC_TARGET_RMS = 0.4
_AGC_MAX_GAIN = 20.0


@dataclass(slots=True)
class _FECSettings:
    config: FECConfig
    interleave_depth: int


@dataclass(slots=True)
class _SymbolSyncResult:
    start_index: int
    samples_per_bit: int
    score: float


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
    """Decode a live BFSK capture using matched filters and preamble alignment."""
    config = {**DEFAULT_PARAMS, **params}
    sample_rate = float(config["sample_rate"])
    bit_rate = float(config["bitrate"])
    freq0 = float(config["freq0"])
    freq1 = float(config["freq1"])
    preamble_bits = str(config.get("preamble_bits", "10101010"))

    fec_settings = _parse_fec_settings(config.get("fec", {}))
    codec = build_codec(fec_settings.config)

    signal = np.asarray(waveform, dtype=np.float32)
    if signal.size == 0:
        return DecodeOutput(payload=b"", metrics={"bit_count": 0, "preamble_bits": len(preamble_bits)})

    conditioned = _apply_agc(signal.copy(), target=_AGC_TARGET_RMS, max_gain=_AGC_MAX_GAIN)
    sync = _synchronize(conditioned, sample_rate, bit_rate, freq0, freq1, preamble_bits)

    metrics: dict[str, Any] = {
        "preamble_bits": len(preamble_bits),
        "bitrate": bit_rate,
        "samples_per_bit": int(round(sample_rate / bit_rate)),
    }

    if sync is None or sync.score < _SYNC_MIN_SCORE:
        metrics.update(
            {
                "bit_count": 0,
                "status": "preamble_not_found",
                "sync_score": float(sync.score) if sync else 0.0,
            }
        )
        return DecodeOutput(payload=b"", metrics=metrics)

    bit_array = _demodulate_bits(conditioned, sync, sample_rate, freq0, freq1)
    metrics.update(
        {
            "bit_count": int(bit_array.size),
            "samples_per_bit": sync.samples_per_bit,
            "sync_score": float(sync.score),
            "sync_start": int(sync.start_index),
        }
    )

    preamble_len = len(preamble_bits)
    if bit_array.size <= preamble_len:
        metrics["status"] = "insufficient_data"
        metrics["data_bits"] = 0
        return DecodeOutput(payload=b"", metrics=metrics)

    if fec_settings.config.scheme == "none":
        data_bits = bit_array[preamble_len:]
        payload = _bits_to_bytes(data_bits)
        metrics["data_bits"] = int(data_bits.size)
        metrics["status"] = "ok"
        return DecodeOutput(payload=payload, metrics=metrics)

    encoded_bits = bit_array[preamble_len:]
    if fec_settings.interleave_depth > 1 and encoded_bits.size:
        encoded_bits = _deinterleave_bits(encoded_bits, fec_settings.interleave_depth)

    decoded_bits, fec_metrics = codec.decode(encoded_bits)

    if decoded_bits.size < _HEADER_BITS:
        metrics["fec"] = {
            **fec_metrics,
            "scheme": fec_settings.config.scheme,
            "status": "header_not_recovered",
        }
        metrics["data_bits"] = 0
        metrics["status"] = "fec_failed"
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
    metrics["status"] = "ok"
    return DecodeOutput(payload=payload, metrics=metrics)


def _apply_agc(signal: Array1D, target: float, max_gain: float) -> Array1D:
    rms = float(np.sqrt(np.mean(signal**2) + 1e-12))
    if rms < 1e-9:
        return signal
    gain = float(np.clip(target / rms, 1.0 / max_gain, max_gain))
    signal *= gain
    return signal


def _synchronize(
    signal: Array1D,
    sample_rate: float,
    bit_rate: float,
    freq0: float,
    freq1: float,
    preamble_bits: str,
) -> _SymbolSyncResult | None:
    expected_bits = _preamble_array(preamble_bits)
    if expected_bits.size == 0:
        return None

    reference = np.where(expected_bits > 0, 1.0, -1.0).astype(np.float32)
    reference_norm = float(np.linalg.norm(reference)) or 1.0

    nominal_spb = sample_rate / bit_rate
    timing_offsets = np.linspace(-_SYNC_TIMING_PCT, _SYNC_TIMING_PCT, _SYNC_TIMING_STEPS)
    candidates = sorted(
        {
            max(_SYNC_MIN_WINDOW, int(round(nominal_spb * (1.0 + offset))))
            for offset in timing_offsets
        }
    )

    best: _SymbolSyncResult | None = None
    for samples_per_bit in candidates:
        kernel = _build_symbol_kernel(samples_per_bit, freq0, freq1, sample_rate)
        total_needed = samples_per_bit * expected_bits.size
        max_start = int(signal.size - total_needed)
        if max_start < 0:
            continue

        coarse_step = max(4, samples_per_bit // 8)
        coarse_candidate = _scan_for_preamble(
            signal,
            kernel,
            expected=reference,
            expected_norm=reference_norm,
            samples_per_bit=samples_per_bit,
            start_min=0,
            start_max=max_start,
            step=coarse_step,
        )
        if coarse_candidate is None:
            continue

        refine_step = max(1, samples_per_bit // 32)
        refined = _scan_for_preamble(
            signal,
            kernel,
            expected=reference,
            expected_norm=reference_norm,
            samples_per_bit=samples_per_bit,
            start_min=max(0, coarse_candidate.start_index - samples_per_bit),
            start_max=min(max_start, coarse_candidate.start_index + samples_per_bit),
            step=refine_step,
        )
        candidate = refined or coarse_candidate
        if best is None or (candidate and candidate.score > best.score):
            best = candidate

    return best


def _scan_for_preamble(
    signal: Array1D,
    kernel: tuple[np.ndarray, np.ndarray, np.ndarray],
    expected: np.ndarray,
    expected_norm: float,
    samples_per_bit: int,
    start_min: int,
    start_max: int,
    step: int,
) -> _SymbolSyncResult | None:
    preamble_len = expected.size
    window, carrier0, carrier1 = kernel
    best: _SymbolSyncResult | None = None

    if start_min > start_max:
        return None

    for start in range(start_min, start_max + 1, max(step, 1)):
        diffs = _symbol_differences(signal, start, window, carrier0, carrier1, preamble_len)
        if diffs.size != preamble_len:
            break
        score = _correlate(diffs, expected, expected_norm)
        if score is None:
            continue
        if best is None or score > best.score:
            best = _SymbolSyncResult(start_index=start, samples_per_bit=samples_per_bit, score=score)
    return best


def _correlate(observed: np.ndarray, reference: np.ndarray, reference_norm: float) -> float | None:
    energy = float(np.linalg.norm(observed))
    if energy < 1e-6:
        return None
    return float(np.dot(observed, reference) / ((energy * reference_norm) + 1e-12))


def _demodulate_bits(
    signal: Array1D,
    sync: _SymbolSyncResult,
    sample_rate: float,
    freq0: float,
    freq1: float,
) -> BitArray:
    samples_per_bit = int(sync.samples_per_bit)
    if samples_per_bit <= 0:
        return np.array([], dtype=np.uint8)

    kernel = _build_symbol_kernel(samples_per_bit, freq0, freq1, sample_rate)
    total_bits = (signal.size - sync.start_index) // samples_per_bit
    if total_bits <= 0:
        return np.array([], dtype=np.uint8)

    bits = np.zeros(total_bits, dtype=np.uint8)
    window, carrier0, carrier1 = kernel
    for idx in range(total_bits):
        start = sync.start_index + idx * samples_per_bit
        end = start + samples_per_bit
        if end > signal.size:
            return bits[:idx]
        segment = signal[start:end]
        diff = _symbol_difference(segment, window, carrier0, carrier1)
        bits[idx] = 1 if diff >= 0.0 else 0
    return bits


def _symbol_differences(
    signal: Array1D,
    start_index: int,
    window: np.ndarray,
    carrier0: np.ndarray,
    carrier1: np.ndarray,
    count: int,
) -> np.ndarray:
    samples_per_bit = window.size
    diffs = np.empty(count, dtype=np.float32)
    for idx in range(count):
        start = start_index + idx * samples_per_bit
        end = start + samples_per_bit
        if end > signal.size:
            return diffs[:idx]
        segment = signal[start:end]
        diffs[idx] = _symbol_difference(segment, window, carrier0, carrier1)
    return diffs


def _symbol_difference(
    segment: Array1D,
    window: np.ndarray,
    carrier0: np.ndarray,
    carrier1: np.ndarray,
) -> float:
    if segment.size != window.size:
        return 0.0
    windowed = segment * window
    energy0 = np.abs(np.dot(windowed, carrier0))
    energy1 = np.abs(np.dot(windowed, carrier1))
    return float(energy1 - energy0)


def _build_symbol_kernel(
    samples_per_bit: int,
    freq0: float,
    freq1: float,
    sample_rate: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    window = _symbol_window(samples_per_bit)
    carrier0 = _carrier(samples_per_bit, freq0, sample_rate)
    carrier1 = _carrier(samples_per_bit, freq1, sample_rate)
    return window, carrier0, carrier1


def _symbol_window(length: int) -> np.ndarray:
    if length <= 3:
        return np.ones(length, dtype=np.float32)
    return np.hanning(length).astype(np.float32)


def _carrier(length: int, freq: float, sample_rate: float) -> np.ndarray:
    if length <= 0:
        return np.array([], dtype=np.complex64)
    positions = np.arange(length, dtype=np.float32)
    angle = 2 * np.pi * freq / sample_rate
    real = np.cos(angle * positions)
    imag = -np.sin(angle * positions)
    return (real + 1j * imag).astype(np.complex64)


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
