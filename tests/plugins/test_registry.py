from __future__ import annotations

from pathlib import Path

from amw.plugins.registry import PluginRegistry


def test_bfsk_plugin_discovery() -> None:
    root = Path(__file__).resolve().parents[2] / "modems"
    registry = PluginRegistry(root=root)
    plugins = registry.discover()
    assert "BFSK Reference" in plugins

    plugin = plugins["BFSK Reference"]
    assert plugin.metadata.sample_rate == 48_000
    assert "bitrate" in plugin.default_params
    assert plugin.schema["title"] == "BFSK Modem Parameters"

    encode_output = plugin.encode(b"hi", plugin.default_params)
    assert encode_output.waveform.size > 0
    assert encode_output.metadata["bit_count"] > 0


def test_plugin_registry_missing_root(tmp_path: Path) -> None:
    registry = PluginRegistry(root=tmp_path / "missing")
    plugins = registry.discover()
    assert plugins == {}
