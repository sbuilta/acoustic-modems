"""Audio and payload I/O utilities."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import-time metadata for type-checkers
    from .audio import AudioService, RecordingResult
    from .payload import PayloadBuilder, PayloadSpec, PayloadType

__all__ = ["AudioService", "PayloadBuilder", "PayloadSpec", "PayloadType", "RecordingResult"]


def __getattr__(name: str) -> Any:
    if name in {"AudioService", "RecordingResult"}:
        module = import_module(".audio", __name__)
        return getattr(module, name)
    if name in {"PayloadBuilder", "PayloadSpec", "PayloadType"}:
        module = import_module(".payload", __name__)
        return getattr(module, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
