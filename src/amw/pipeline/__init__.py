"""Signal processing pipeline for the Acoustic Modem Workbench."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .artifacts import PipelineArtifacts, PipelineState

if TYPE_CHECKING:  # pragma: no cover - imported by type-checkers only
    from .orchestrator import PipelineOrchestrator

__all__ = ["PipelineArtifacts", "PipelineOrchestrator", "PipelineState"]


def __getattr__(name: str) -> Any:
    if name == "PipelineOrchestrator":
        module = import_module(".orchestrator", __name__)
        return getattr(module, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
