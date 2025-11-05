from __future__ import annotations

import pytest

from amw.io.audio import AudioService
import amw.pipeline as pipeline_pkg
from amw.pipeline import PipelineOrchestrator
from amw.plugins.registry import PluginRegistry


def test_pipeline_package_exports() -> None:
    registry = PluginRegistry()
    orchestrator = PipelineOrchestrator(registry, AudioService())
    assert orchestrator.state.name == "IDLE"


def test_pipeline_package_missing_attr() -> None:
    with pytest.raises(AttributeError):
        _ = pipeline_pkg.missing