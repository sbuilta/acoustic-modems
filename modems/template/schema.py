"""Helpers for loading template plugin schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    """Load the plugin parameter schema from disk."""
    return json.loads((_HERE / "schema.json").read_text())


@lru_cache(maxsize=1)
def load_defaults() -> dict[str, Any]:
    """Load default parameter values."""
    return json.loads((_HERE / "defaults.json").read_text())
