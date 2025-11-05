"""Plugin discovery and contracts for modem implementations."""

from .contract import DecodeOutput, EncodeOutput, PluginHandle, PluginMetadata
from .registry import PluginRegistry

__all__ = ["DecodeOutput", "EncodeOutput", "PluginHandle", "PluginMetadata", "PluginRegistry"]
