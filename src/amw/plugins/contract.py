"""Shared modem plugin contract definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt

Array1D = npt.NDArray[np.float32]


@dataclass(slots=True)
class PluginMetadata:
    """Descriptive metadata surfaced to the GUI."""

    name: str
    version: str
    sample_rate: int
    description: str = ""
    author: str | None = None
    license: str | None = None


@dataclass(slots=True)
class EncodeOutput:
    """Return type for modem encode functions."""

    waveform: Array1D
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DecodeOutput:
    """Return type for modem decode functions."""

    payload: bytes
    metrics: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class EncoderCallable(Protocol):
    """Signature expected for plugin encode functions."""

    def __call__(self, payload: bytes, params: dict[str, Any]) -> EncodeOutput:
        ...


@runtime_checkable
class DecoderCallable(Protocol):
    """Signature expected for plugin decode functions."""

    def __call__(self, waveform: Array1D, params: dict[str, Any]) -> DecodeOutput:
        ...


@dataclass(slots=True)
class PluginHandle:
    """Aggregates references and metadata for a modem plugin."""

    metadata: PluginMetadata
    encode: EncoderCallable
    decode: DecoderCallable
    schema: dict[str, Any]
    default_params: dict[str, Any]

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def sample_rate(self) -> int:
        return self.metadata.sample_rate
