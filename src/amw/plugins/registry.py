"""Discovery utilities for modem plugins."""

from __future__ import annotations

import importlib
from pathlib import Path

from loguru import logger

from .contract import PluginHandle, PluginMetadata


def _coerce_metadata(raw: PluginMetadata | dict | None, fallback_name: str) -> PluginMetadata:
    if isinstance(raw, PluginMetadata):
        return raw
    if isinstance(raw, dict):
        return PluginMetadata(**raw)
    logger.warning("Plugin '%s' missing PLUGIN_METADATA, synthesizing placeholder.", fallback_name)
    return PluginMetadata(name=fallback_name, version="0.0.0", sample_rate=48_000)


class PluginRegistry:
    """Loads modem implementations from the `modems/` directory."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root else Path(__file__).resolve().parents[3] / "modems"
        self._plugins: dict[str, PluginHandle] = {}

    def discover(self) -> dict[str, PluginHandle]:
        """Scan the filesystem and import plugin modules."""
        self._plugins.clear()
        if not self._root.exists():
            logger.warning("Plugin root '%s' does not exist.", self._root)
            return self._plugins

        for path in sorted(self._root.iterdir()):
            if not path.is_dir() or path.name.startswith("_") or path.name == "template":
                continue
            module_name = f"modems.{path.name}"
            try:
                module = importlib.import_module(module_name)
                schema_module = importlib.import_module(f"{module_name}.schema")
            except ModuleNotFoundError as exc:
                logger.error("Failed to import modem plugin '%s': %s", path.name, exc)
                continue

            encode = getattr(module, "encode", None)
            decode = getattr(module, "decode", None)
            schema_dict = getattr(schema_module, "PARAM_SCHEMA", None)
            default_params = getattr(module, "DEFAULT_PARAMS", {})
            metadata = _coerce_metadata(getattr(module, "PLUGIN_METADATA", None), path.name)

            if not _is_callable(encode) or not _is_callable(decode) or schema_dict is None:
                logger.error("Plugin '%s' missing required exports.", path.name)
                continue

            handle = PluginHandle(
                metadata=metadata,
                encode=encode,
                decode=decode,
                schema=schema_dict,
                default_params=default_params,
            )
            self._plugins[handle.name] = handle
            logger.debug("Registered modem plugin '%s'", handle.name)
        return self._plugins

    def get(self, name: str) -> PluginHandle | None:
        """Return the plugin handle by name, populating the cache if needed."""
        if not self._plugins:
            self.discover()
        return self._plugins.get(name)

    def all(self) -> dict[str, PluginHandle]:
        """Return all discovered plugins."""
        if not self._plugins:
            self.discover()
        return dict(self._plugins)


def _is_callable(func: object) -> bool:
    return callable(func)
