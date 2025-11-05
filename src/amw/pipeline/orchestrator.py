"""Primary orchestrator managing the modem pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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

    def record(self, duration: float, use_trigger: bool = False) -> RecordingResult:
        """Record from the selected device."""
        context = self._require_context()
        self.state = PipelineState.RECORDING
        result = self._audio.record(duration=duration, sample_rate=context.plugin.sample_rate, use_trigger=use_trigger)
        self.artifacts.rx_raw = result.samples
        self.artifacts.metadata["record"] = result.metadata
        return result

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
