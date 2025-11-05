"""Acoustic Modem Workbench application package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("acoustic-modem-workbench")
except PackageNotFoundError:  # pragma: no cover - resolved once installed
    __version__ = "0.0.0"

__all__ = ["__version__"]
