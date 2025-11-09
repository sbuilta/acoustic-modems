"""Primary orchestrator managing the modem pipeline."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

import numpy as np
from loguru import logger

from amw.io.audio import AudioService, RecordingResult
from amw.io.payload import PayloadBuilder, PayloadSpec
from amw.pipeline.artifacts import PipelineArtifacts, PipelineState
from amw.pipeline.conditioner import ConditionHints, Conditioner
from amw.plugins.contract import DecodeOutput, EncodeOutput, PluginHandle
from amw.plugins.registry import PluginRegistry


@dataclass(slots=True)
class PipelineContext:
    """Runtime context describing the currently selected modem and payload."""

    plugin: PluginHandle
    params: dict
    payload_spec: PayloadSpec


class PipelineOrchestrator:
    """Coordinates build → transmit → record → condition → decode operations."""

    def __init__(
        self,
        registry: PluginRegistry,
        audio_service: AudioService,
        conditioner: Conditioner | None = None,
        payload_builder: PayloadBuilder | None = None,
    ) -> None:
        self._registry = registry
        self._audio = audio_service
        self._conditioner = conditioner or Conditioner()
        self._payload_builder = payload_builder or PayloadBuilder()
        self._context: PipelineContext | None = None
        self.state = PipelineState.IDLE
        self.artifacts = PipelineArtifacts()

    def configure(self, plugin_name: str, params: dict, payload_spec: PayloadSpec) -> None:
        """Select a modem plugin and payload specification for subsequent runs."""
        plugin = self._registry.get(plugin_name)
        if plugin is None:
            raise ValueError(f"Unknown modem plugin '{plugin_name}'")
        self._context = PipelineContext(plugin=plugin, params=params, payload_spec=payload_spec)
        self.state = PipelineState.IDLE
        self.artifacts.clear()
        logger.debug("Configured pipeline with plugin '{}' and payload {}", plugin_name, payload_spec.mode)

    def build(self) -> EncodeOutput:
        """Generate the transmit waveform using the selected plugin."""
        context = self._require_context()
        payload_bytes = self._payload_builder.build(context.payload_spec)
        encode_output = context.plugin.encode(payload_bytes, context.params)
        self.artifacts.tx_waveform = encode_output.waveform
        self.artifacts.metadata["encode"] = encode_output.metadata
        self.state = PipelineState.BUILT
        return encode_output

    def transmit(self, gain: float = 1.0) -> None:
        """Play the previously built waveform to the output device."""
        if self.artifacts.tx_waveform is None:
            raise RuntimeError("Build step must precede transmit.")
        self.state = PipelineState.TRANSMITTING
        self._audio.play(self.artifacts.tx_waveform, gain=gain)
        logger.info("Transmit complete")

    def record(
        self,
        duration: float | None,
        *,
        use_trigger: bool = False,
        stop_condition: Callable[[], bool] | None = None,
        silence_timeout: float | None = None,
        chunk_duration: float = 0.5,
        silence_threshold: float = 1e-3,
    ) -> RecordingResult:
        """Record from the selected device.

        When stop_condition or silence_timeout is provided, the orchestrator streams shorter
        chunks until the callback requests a stop, the silence timeout elapses, or the
        optional maximum duration (duration argument) is reached.
        """
        context = self._require_context()
        sample_rate = context.plugin.sample_rate
        self.state = PipelineState.RECORDING

        if stop_condition is None and silence_timeout is None:
            if duration is None:
                raise ValueError("duration is required when no stop/silence criteria are provided.")
            result = self._audio.record(duration=duration, sample_rate=sample_rate, use_trigger=use_trigger)
            self.artifacts.rx_raw = result.samples
            self.artifacts.metadata["record"] = result.metadata
            return result

        streaming = self._record_streaming(
            sample_rate=sample_rate,
            max_duration=duration,
            use_trigger=use_trigger,
            stop_condition=stop_condition,
            silence_timeout=silence_timeout,
            chunk_duration=chunk_duration,
            silence_threshold=silence_threshold,
        )
        self.artifacts.rx_raw = streaming.samples
        self.artifacts.metadata["record"] = streaming.metadata
        return streaming

    def condition(self, hints: Optional[ConditionHints] = None):
        """Condition the recorded waveform."""
        if self.artifacts.rx_raw is None:
            raise RuntimeError("No recording to condition.")
        context = self._require_context()
        conditioned = self._conditioner.condition(self.artifacts.rx_raw, context.plugin.sample_rate, hints)
        self.artifacts.rx_conditioned = conditioned.waveform
        self.artifacts.metadata["condition"] = conditioned.metrics
        self.state = PipelineState.CONDITIONED
        return conditioned

    def decode(self) -> DecodeOutput:
        """Decode the conditioned waveform using the modem plugin."""
        if self.artifacts.rx_conditioned is None:
            raise RuntimeError("Conditioning must run before decode.")
        context = self._require_context()
        decode_output = context.plugin.decode(self.artifacts.rx_conditioned, context.params)
        self.artifacts.decoded_payload = decode_output.payload
        self.artifacts.metadata["decode"] = decode_output.metrics
        self.state = PipelineState.DECODED
        return decode_output

    def _require_context(self) -> PipelineContext:
        if self._context is None:
            raise RuntimeError("Pipeline not configured with a modem and payload.")
        return self._context

    def _record_streaming(
        self,
        *,
        sample_rate: int,
        max_duration: float | None,
        use_trigger: bool,
        stop_condition: Callable[[], bool] | None,
        silence_timeout: float | None,
        chunk_duration: float,
        silence_threshold: float,
    ) -> RecordingResult:
        """Iteratively record until a stop signal, silence timeout, or max duration occurs."""
        if chunk_duration <= 0:
            raise ValueError("chunk_duration must be positive.")
        if stop_condition is None and (silence_timeout is None or silence_timeout <= 0):
            raise ValueError("Streaming record requires stop_condition or silence_timeout.")

        chunk_duration = float(chunk_duration)
        chunk_samples = max(int(chunk_duration * sample_rate), 1)
        silence_limit = int((silence_timeout or 0) * sample_rate)
        max_samples = int(max_duration * sample_rate) if max_duration else None

        collected: list[np.ndarray] = []
        total_samples = 0
        trailing_silence = 0
        stop_reason = None
        chunk_count = 0
        last_metadata: dict[str, object] | None = None
        trigger_flag = use_trigger

        while True:
            if stop_condition and stop_condition():
                stop_reason = "user"
                break

            if max_samples is not None and total_samples >= max_samples:
                stop_reason = "duration"
                break

            result = self._audio.record(
                duration=chunk_samples / sample_rate,
                sample_rate=sample_rate,
                use_trigger=trigger_flag,
            )
            trigger_flag = False
            chunk_count += 1
            collected.append(result.samples)
            total_samples += result.samples.size
            last_metadata = result.metadata

            if stop_condition and stop_condition():
                stop_reason = "user"
                break

            if silence_limit > 0:
                trailing_silence = self._update_trailing_silence(result.samples, trailing_silence, silence_threshold)
                if trailing_silence >= silence_limit:
                    stop_reason = "silence"
                    break

        if stop_reason is None:
            stop_reason = "completed"

        samples = np.concatenate(collected, axis=0) if collected else np.zeros(0, dtype=np.float32)
        metadata: dict[str, object] = dict(last_metadata or {})
        metadata.update(
            {
                "stop_reason": stop_reason,
                "chunks": chunk_count,
                "sample_rate": sample_rate,
                "silence_timeout_s": silence_timeout,
                "max_duration_s": max_duration,
                "captured_duration_s": samples.size / sample_rate if sample_rate else 0.0,
            }
        )
        return RecordingResult(samples=samples, sample_rate=sample_rate, metadata=metadata)

    @staticmethod
    def _update_trailing_silence(samples: np.ndarray, current: int, threshold: float) -> int:
        """Track the number of trailing silent samples across consecutive chunks."""
        if samples.size == 0:
            return current
        above_threshold = np.flatnonzero(np.abs(samples) > threshold)
        if above_threshold.size == 0:
            return current + samples.size
        last_loud = int(above_threshold[-1])
        trailing = samples.size - (last_loud + 1)
        return trailing
