"""Warehouse path discovery and connection helpers.

The SDK intentionally uses stdlib `sqlite3` rather than Django ORM so it can
be imported into a Jupyter kernel with only two deps (`sqlite3`, `pandas`).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


class WarehouseNotFound(FileNotFoundError):
    """Raised when the SDK can't locate the warehouse.db file."""


def resolve_warehouse_path(override: str | os.PathLike | None = None) -> Path:
    """Return an absolute path to warehouse.db.

    Resolution order:
      1. `override` argument (if given, must exist).
      2. `FORECASTER_DB_PATH` environment variable.
      3. Walk upward from cwd looking for a `data/warehouse.db` file.
    """
    if override is not None:
        p = Path(override).expanduser().resolve()
        if not p.exists():
            raise WarehouseNotFound(f"override path does not exist: {p}")
        return p

    env = os.environ.get("FORECASTER_DB_PATH")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            raise WarehouseNotFound(
                f"FORECASTER_DB_PATH points at missing file: {p}"
            )
        return p

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        db = candidate / "data" / "warehouse.db"
        if db.exists():
            return db

    raise WarehouseNotFound(
        "Could not find data/warehouse.db by walking up from the current "
        "working directory. Set FORECASTER_DB_PATH or pass db_path= explicitly. "
        "(Did you run `make migrate`?)"
    )


def connect(db_path: str | os.PathLike | None = None) -> sqlite3.Connection:
    """Open a connection with sensible defaults for our use case."""
    path = resolve_warehouse_path(db_path)
    conn = sqlite3.connect(str(path), isolation_level=None, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL lets many readers + one writer coexist during long research sessions.
    conn.execute("PRAGMA journal_mode = WAL")
    return conn
