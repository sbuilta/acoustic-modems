from __future__ import annotations

from pathlib import Path

import numpy as np

from amw.io.audio import AudioService, RecordingResult
from amw.io.payload import PayloadBuilder, PayloadSpec, PayloadType
from amw.pipeline import PipelineOrchestrator
from amw.plugins.registry import PluginRegistry


class DummyAudio(AudioService):
    def __init__(self) -> None:
        super().__init__()
        self.play_invocations = 0

    def play(self, waveform: np.ndarray, sample_rate: int = 48_000, gain: float = 1.0) -> None:  # type: ignore[override]
        self.play_invocations += 1

    def record(self, duration: float, sample_rate: int, use_trigger: bool = False) -> RecordingResult:  # type: ignore[override]
        frames = int(duration * sample_rate)
        samples = np.zeros(frames, dtype=np.float32)
        return RecordingResult(samples=samples, sample_rate=sample_rate, metadata={"simulated": True})


class ChunkedAudio(AudioService):
    def __init__(self, chunks: list[np.ndarray]) -> None:
        super().__init__()
        self._chunks = list(chunks)
        self.play_invocations = 0

    def play(self, waveform: np.ndarray, sample_rate: int = 48_000, gain: float = 1.0) -> None:  # type: ignore[override]
        self.play_invocations += 1

    def record(self, duration: float, sample_rate: int, use_trigger: bool = False) -> RecordingResult:  # type: ignore[override]
        if self._chunks:
            samples = self._chunks.pop(0)
        else:
            frames = int(duration * sample_rate)
            samples = np.zeros(frames, dtype=np.float32)
        return RecordingResult(samples=samples, sample_rate=sample_rate, metadata={"simulated": True})


def test_pipeline_happy_path() -> None:
    root = Path(__file__).resolve().parents[2] / "modems"
    registry = PluginRegistry(root=root)
    plugin = registry.get("BFSK Reference")
    assert plugin is not None

    audio = DummyAudio()
    payload_spec = PayloadSpec(mode=PayloadType.TEXT, text="test", crc=False)
    orchestrator = PipelineOrchestrator(registry, audio, payload_builder=PayloadBuilder())
    orchestrator.configure("BFSK Reference", plugin.default_params, payload_spec)

    encode_output = orchestrator.build()
    assert encode_output.waveform.size > 0

    orchestrator.transmit()
    assert audio.play_invocations == 1

    recording = orchestrator.record(duration=0.01)
    assert recording.samples.size == int(0.01 * plugin.metadata.sample_rate)

    conditioned = orchestrator.condition()
    assert conditioned.waveform.shape == recording.samples.shape

    decode_output = orchestrator.decode()
    assert isinstance(decode_output.payload, bytes)


def test_record_streams_until_silence() -> None:
    root = Path(__file__).resolve().parents[2] / "modems"
    registry = PluginRegistry(root=root)
    plugin = registry.get("BFSK Reference")
    assert plugin is not None

    sample_rate = plugin.metadata.sample_rate
    chunk = int(0.5 * sample_rate)
    loud = np.ones(chunk, dtype=np.float32)
    silent = np.zeros(chunk, dtype=np.float32)
    audio = ChunkedAudio([loud, silent, silent])

    payload_spec = PayloadSpec(mode=PayloadType.TEXT, text="loop", crc=False)
    orchestrator = PipelineOrchestrator(registry, audio, payload_builder=PayloadBuilder())
    orchestrator.configure("BFSK Reference", plugin.default_params, payload_spec)

    result = orchestrator.record(
        duration=5.0,
        silence_timeout=1.0,
        stop_condition=None,
        chunk_duration=0.5,
    )

    assert result.metadata["stop_reason"] == "silence"
    assert result.samples.size == chunk * 3


def test_record_honors_stop_request() -> None:
    root = Path(__file__).resolve().parents[2] / "modems"
    registry = PluginRegistry(root=root)
    plugin = registry.get("BFSK Reference")
    assert plugin is not None

    sample_rate = plugin.metadata.sample_rate
    chunk = int(0.25 * sample_rate)
    audio = ChunkedAudio([np.ones(chunk, dtype=np.float32) for _ in range(5)])

    payload_spec = PayloadSpec(mode=PayloadType.TEXT, text="loop", crc=False)
    orchestrator = PipelineOrchestrator(registry, audio, payload_builder=PayloadBuilder())
    orchestrator.configure("BFSK Reference", plugin.default_params, payload_spec)

    calls = {"count": 0}

    def stop_condition() -> bool:
        calls["count"] += 1
        return calls["count"] > 2

    result = orchestrator.record(
        duration=5.0,
        stop_condition=stop_condition,
        silence_timeout=None,
        chunk_duration=0.25,
    )

    assert result.metadata["stop_reason"] == "user"
    assert result.samples.size >= chunk * 3
