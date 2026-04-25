"""The Run context manager — the SDK's main public surface."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from tracker.db import connect


class Run:
    """Handle to a logical experiment run. Obtained via the `run(...)`
    context manager; do not instantiate directly."""

    def __init__(self, conn: sqlite3.Connection, run_id: str, experiment_id: int):
        self._conn = conn
        self.run_id = run_id
        self.experiment_id = experiment_id

    # -------- params --------

    def param(self, key: str, value: Any) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO run_param (run_id, key, value_json) VALUES (?, ?, ?)",
            (self.run_id, key, json.dumps(value, default=str)),
        )

    def params(self, mapping: Mapping[str, Any]) -> None:
        for k, v in mapping.items():
            self.param(k, v)

    # -------- metrics --------

    def log_metric(self, key: str, value: float, step: int = 0) -> None:
        self._conn.execute(
            "INSERT INTO run_metric (run_id, key, value, step, ts) VALUES (?, ?, ?, ?, ?)",
            (self.run_id, key, float(value), int(step), _now_iso()),
        )

    def log_metrics(self, mapping: Mapping[str, float], step: int = 0) -> None:
        for k, v in mapping.items():
            self.log_metric(k, v, step=step)

    # -------- tags --------

    def tag(self, *tags: str) -> None:
        for t in tags:
            self._conn.execute(
                "INSERT OR IGNORE INTO run_tag (run_id, tag) VALUES (?, ?)",
                (self.run_id, t),
            )

    # -------- feature importance --------

    def log_importance(self, importances: Any) -> None:
        """Accept a dict {feature: score}, a pandas Series, or a 2-col DataFrame."""
        pairs = _coerce_importances(importances)
        ordered = sorted(pairs, key=lambda kv: -abs(kv[1]))
        for rank, (feat, imp) in enumerate(ordered, start=1):
            self._conn.execute(
                "INSERT OR REPLACE INTO run_feature_importance "
                "(run_id, feature, importance, rank) VALUES (?, ?, ?, ?)",
                (self.run_id, feat, float(imp), rank),
            )

    # -------- artifacts --------

    def log_artifact(self, name: str, path: str | os.PathLike, kind: str = "") -> None:
        p = Path(path)
        size = p.stat().st_size if p.exists() else 0
        self._conn.execute(
            "INSERT OR REPLACE INTO run_artifact "
            "(run_id, name, path, kind, size_bytes) VALUES (?, ?, ?, ?, ?)",
            (self.run_id, name, str(p), kind, int(size)),
        )


@contextmanager
def attach(
    run_id: str,
    *,
    db_path: str | os.PathLike | None = None,
) -> Iterator[Run]:
    """Open a handle to an existing run to log additional params/metrics/artifacts.

    Does not change the run's status or finished_at; use this for downstream
    passes (e.g. portfolio backtest writing metrics back to the RF run that
    produced the picks). Accepts either 32-hex (Django form) or dashed UUID.
    """
    normalized = run_id.replace("-", "")
    conn = connect(db_path)
    row = conn.execute(
        "SELECT experiment_id FROM run WHERE run_id = ?", (normalized,)
    ).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"run_id not found: {run_id}")
    r = Run(conn, normalized, int(row["experiment_id"]))
    try:
        yield r
    finally:
        conn.close()


@contextmanager
def run(
    experiment: str,
    *,
    params: Mapping[str, Any] | None = None,
    tags: Iterable[str] | None = None,
    name: str = "",
    db_path: str | os.PathLike | None = None,
    description: str = "",
) -> Iterator[Run]:
    """Begin a tracked run. Writes `running` row on enter, flips to
    `completed` (or `failed`) on exit. Exceptions propagate after logging."""
    conn = connect(db_path)
    started = _now_iso()
    # Use hex (no dashes, 32 chars) — matches how Django's UUIDField serialises
    # to SQLite, so ORM-side FK joins match SDK-side inserts.
    run_id = uuid.uuid4().hex
    experiment_id = _get_or_create_experiment(conn, experiment, description)
    git = _git_sha()

    conn.execute(
        "INSERT INTO run "
        "(run_id, experiment_id, name, status, started_at, git_sha, error, finished_at) "
        "VALUES (?, ?, ?, 'running', ?, ?, '', NULL)",
        (run_id, experiment_id, name, started, git),
    )

    r = Run(conn, run_id, experiment_id)
    if params:
        r.params(params)
    if tags:
        r.tag(*tags)

    try:
        yield r
    except BaseException as exc:
        err = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        conn.execute(
            "UPDATE run SET status='failed', finished_at=?, error=? WHERE run_id=?",
            (_now_iso(), err[:4000], run_id),
        )
        conn.close()
        raise
    else:
        conn.execute(
            "UPDATE run SET status='completed', finished_at=? WHERE run_id=?",
            (_now_iso(), run_id),
        )
        conn.close()


# -------- internals --------


def _get_or_create_experiment(
    conn: sqlite3.Connection, name: str, description: str
) -> int:
    row = conn.execute(
        "SELECT experiment_id FROM experiment WHERE name = ?", (name,)
    ).fetchone()
    if row:
        return int(row["experiment_id"])
    cur = conn.execute(
        "INSERT INTO experiment (name, description, created_at) VALUES (?, ?, ?)",
        (name, description, _now_iso()),
    )
    return int(cur.lastrowid)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )
        if out.returncode == 0:
            return out.stdout.strip()[:40]
    except Exception:
        pass
    return ""


def _coerce_importances(obj: Any) -> list[tuple[str, float]]:
    """Accept dict, pandas.Series, or 2-column DataFrame."""
    if isinstance(obj, Mapping):
        return [(str(k), float(v)) for k, v in obj.items()]
    # Duck-type pandas without importing it unconditionally.
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            d = to_dict()
            if isinstance(d, Mapping):
                return [(str(k), float(v)) for k, v in d.items()]
        except Exception:
            pass
    values = getattr(obj, "values", None)
    index = getattr(obj, "index", None)
    if values is not None and index is not None:
        return [(str(k), float(v)) for k, v in zip(index, values)]
    raise TypeError(
        "log_importance expects a dict, pandas Series, or 2-col DataFrame"
    )
