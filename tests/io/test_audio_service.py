from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from amw.io.audio import AudioService


def test_audio_service_play_without_sd(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr("amw.io.audio.sd", None)
    service = AudioService()
    waveform = np.ones(4, dtype=np.float32)
    with caplog.at_level("WARNING"):
        service.play(waveform, gain=0.5)
    # No scaling should mutate the original buffer
    assert np.array_equal(waveform, np.ones(4, dtype=np.float32))


def test_audio_service_record_without_sd(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("amw.io.audio.sd", None)
    service = AudioService()
    result = service.record(duration=0.01, sample_rate=1000)
    assert result.samples.size == 10
    assert result.metadata["simulated"] is True


def test_audio_service_with_stubbed_sd(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, np.ndarray] = {}

    def fake_play(data: np.ndarray, samplerate: int, device: int | None, blocking: bool) -> None:
        captured["play"] = data
        captured["samplerate"] = samplerate
        captured["device"] = device
        captured["blocking"] = blocking

    def fake_rec(frames: int, samplerate: int, channels: int, dtype: str, device: int | None) -> np.ndarray:
        assert dtype == "float32"
        captured["rec_args"] = (frames, samplerate, channels, device)
        return np.ones((frames, channels), dtype=np.float32)

    sd_stub = SimpleNamespace(play=fake_play, rec=fake_rec, wait=lambda: None)
    monkeypatch.setattr("amw.io.audio.sd", sd_stub)

    service = AudioService(output_device=2, input_device=3)
    waveform = np.array([0.0, 0.5, 1.0], dtype=np.float32)
    service.play(waveform, sample_rate=2000, gain=2.0)
    assert np.allclose(captured["play"], waveform * 2.0)
    assert captured["samplerate"] == 2000
    assert captured["device"] == 2
    assert captured["blocking"] is True

    result = service.record(duration=0.002, sample_rate=2000, use_trigger=True)
    assert result.samples.size == 4
    assert captured["rec_args"] == (4, 2000, 1, 3)
    assert result.metadata == {"channels": 1, "triggered": True}
