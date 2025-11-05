from __future__ import annotations

from amw.plugins import schema


def test_coalesce_defaults_extracts_values() -> None:
    example_schema = {
        "type": "object",
        "properties": {
            "alpha": {"type": "number", "default": 1.0},
            "beta": {"type": "integer"}
        }
    }
    defaults = schema.coalesce_defaults(example_schema)
    assert defaults == {"alpha": 1.0}


def test_validate_params_passes_well_formed_instance() -> None:
    schema.validate_params({"alpha": 1}, {"type": "object", "properties": {"alpha": {"type": "integer"}}})
