"""Reference implementation template for AMW modem plugins."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from amw.plugins.contract import DecodeOutput, EncodeOutput, PluginMetadata

from .schema import load_defaults, load_schema

Array1D = npt.NDArray[np.float32]

PLUGIN_METADATA = PluginMetadata(
    name="Template Modem",
    version="0.0.1",
    sample_rate=48_000,
    description="Scaffold for authoring new modem plugins.",
    author="Acoustic Modem Workbench",
    license="MIT",
)

PARAM_SCHEMA = load_schema()
DEFAULT_PARAMS = load_defaults()


def encode(payload: bytes, params: dict[str, Any]) -> EncodeOutput:
    """Convert the payload into a waveform ready for playback."""
    raise NotImplementedError("Template plugin does not implement encode().")


def decode(waveform: Array1D, params: dict[str, Any]) -> DecodeOutput:
    """Recover the payload from a conditioned waveform."""
    raise NotImplementedError("Template plugin does not implement decode().")
