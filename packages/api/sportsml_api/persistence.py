"""SQLite-backed run persistence.

In production this is Supabase Postgres with RLS. For v0 we use a single
SQLite file at ``${SPORTSML_DATA_DIR}/runs.db`` with the same schema shape
so the migration to Postgres is mechanical.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sportsml.core.models.runs import ModelRun, ModelRunStatus

if TYPE_CHECKING:
    from collections.abc import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS model_runs (
    run_id          TEXT PRIMARY KEY,
    model_id        TEXT NOT NULL,
    tenant_id       TEXT NOT NULL,
    config_hash     TEXT NOT NULL,
    config_json     TEXT NOT NULL,
    status          TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    duration_s      REAL,
    row_count       INTEGER,
    output_dataset  TEXT,
    error           TEXT,
    label           TEXT
);
CREATE INDEX IF NOT EXISTS idx_model_runs_model ON model_runs(model_id);
CREATE INDEX IF NOT EXISTS idx_model_runs_hash  ON model_runs(model_id, config_hash);
"""


def _db_path() -> Path:
    return Path(os.environ.get("SPORTSML_DATA_DIR", "./data")).resolve() / "runs.db"


def init_runs_db() -> None:
    p = _db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(p) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    p = _db_path()
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _serialize(run: ModelRun) -> dict[str, object]:
    d = asdict(run)
    d["status"] = run.status.value
    d["started_at"] = run.started_at.isoformat()
    if run.finished_at:
        d["finished_at"] = run.finished_at.isoformat()
    return d


def _deserialize(row: sqlite3.Row) -> ModelRun:
    return ModelRun(
        run_id=row["run_id"],
        model_id=row["model_id"],
        tenant_id=row["tenant_id"],
        config_hash=row["config_hash"],
        config_json=row["config_json"],
        status=ModelRunStatus(row["status"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
        duration_s=row["duration_s"],
        row_count=row["row_count"],
        output_dataset=row["output_dataset"],
        error=row["error"],
        label=row["label"],
    )


def insert_run(run: ModelRun) -> None:
    d = _serialize(run)
    with connection() as c:
        c.execute(
            """
            INSERT INTO model_runs
            (run_id, model_id, tenant_id, config_hash, config_json, status,
             started_at, finished_at, duration_s, row_count, output_dataset,
             error, label)
            VALUES (:run_id, :model_id, :tenant_id, :config_hash, :config_json,
                    :status, :started_at, :finished_at, :duration_s, :row_count,
                    :output_dataset, :error, :label)
            """,
            d,
        )
        c.commit()


def update_run(run: ModelRun) -> None:
    d = _serialize(run)
    with connection() as c:
        c.execute(
            """
            UPDATE model_runs SET
                status = :status,
                finished_at = :finished_at,
                duration_s = :duration_s,
                row_count = :row_count,
                output_dataset = :output_dataset,
                error = :error
            WHERE run_id = :run_id
            """,
            d,
        )
        c.commit()


def get_run(run_id: str) -> ModelRun | None:
    with connection() as c:
        row = c.execute(
            "SELECT * FROM model_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
    return _deserialize(row) if row else None


def find_run_by_hash(model_id: str, tenant_id: str, config_hash: str) -> ModelRun | None:
    """Return the most recent succeeded run for a given config_hash, or None."""
    with connection() as c:
        row = c.execute(
            """
            SELECT * FROM model_runs
            WHERE model_id = ? AND tenant_id = ? AND config_hash = ?
              AND status = 'succeeded'
            ORDER BY started_at DESC LIMIT 1
            """,
            (model_id, tenant_id, config_hash),
        ).fetchone()
    return _deserialize(row) if row else None


def compute_config_hash(model_id: str, config: dict) -> str:
    """Stable hash over (model_id, canonical-JSON of config) for caching."""
    import hashlib

    payload = json.dumps({"model_id": model_id, "config": config}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
