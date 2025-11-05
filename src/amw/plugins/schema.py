"""Utilities for working with plugin parameter schemas."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator


def validate_params(params: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    """Raise if the provided params do not conform to the plugin schema."""
    validator = Draft202012Validator(schema)
    validator.validate(params)


def coalesce_defaults(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Extract default values from the JSON schema properties section."""
    defaults: dict[str, Any] = {}
    properties = schema.get("properties", {})
    for key, meta in properties.items():
        if isinstance(meta, Mapping) and "default" in meta:
            defaults[key] = meta["default"]
    return defaults
