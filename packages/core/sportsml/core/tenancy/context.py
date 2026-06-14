"""Environment-driven TenantContext factory.

v0: single demo tenant, single sport. Multi-tenant routing logic lives here
for when auth + JWT claims arrive in v0.5.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
from sportsml.core.models.context import TenantContext

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True, slots=True)
class TenancySettings:
    """Resolved environment configuration for tenancy + storage."""

    tenant_id: str
    sport_id: str
    data_dir: Path
    duckdb_path: Path


def default_settings() -> TenancySettings:
    """Read tenancy settings from environment with v0 defaults."""
    data_dir = Path(os.environ.get("SPORTSML_DATA_DIR", "./data")).resolve()
    duckdb_path = Path(
        os.environ.get("SPORTSML_DUCKDB_PATH", str(data_dir / "sportsml.duckdb"))
    ).resolve()
    return TenancySettings(
        tenant_id=os.environ.get("SPORTSML_TENANT_ID", "demo"),
        sport_id=os.environ.get("SPORTSML_DEFAULT_SPORT", "basketball.nba"),
        data_dir=data_dir,
        duckdb_path=duckdb_path,
    )


@contextmanager
def build_context(
    settings: TenancySettings | None = None,
) -> Iterator[TenantContext]:
    """Construct a TenantContext with an open DuckDB connection.

    Use as a context manager so the connection is always closed:

        with build_context() as ctx:
            ctx.duckdb_conn.execute("SELECT 1")
    """
    s = settings or default_settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    s.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(s.duckdb_path))
    try:
        yield TenantContext(
            tenant_id=s.tenant_id,
            sport_id=s.sport_id,
            duckdb_conn=conn,
            data_dir=s.data_dir,
        )
    finally:
        conn.close()
