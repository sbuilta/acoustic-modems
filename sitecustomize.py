"""Project-wide interpreter customization.

This module ensures that ``sqlite3`` is always importable even when the
interpreter was built without the optional SQLite extension. Some CI
environments omit the required system libraries causing the standard
``sqlite3`` module to fail during import. Coverage.py depends on SQLite
support, so we transparently fall back to the third-party
``pysqlite3-binary`` package when necessary.
"""

from __future__ import annotations

import sys

try:
    import sqlite3 as _sqlite3  # noqa: F401
except ModuleNotFoundError:
    import pysqlite3 as _sqlite3  # type: ignore

    sys.modules["sqlite3"] = _sqlite3
    sys.modules["sqlite3.dbapi2"] = _sqlite3
