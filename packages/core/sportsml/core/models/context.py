"""TenantContext — the universal runtime handle.

Every model run, API call, and ingestion task receives one. It carries:
- tenant_id and sport_id (multi-tenancy + sport plug-in routing)
- a DuckDB connection scoped to the tenant's schema
- the local data directory root
- helpers for writing model outputs and resolving RunRefs

Nothing in core may construct a sport-specific context; build from env via
``sportsml.core.tenancy.context.build_context``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import duckdb
    import pandas as pd


@dataclass(slots=True)
class TenantContext:
    """Runtime context for tenant- and sport-scoped operations.

    Attributes:
        tenant_id: Stable tenant identifier; "demo" in v0.
        sport_id: Dotted sport key (e.g. ``"basketball.nba"``).
        duckdb_conn: Open DuckDB connection. Caller owns close.
        data_dir: Root for Parquet output (Hive-partitioned).
        runrefs: In-memory map of ``field_name -> dataset_name`` resolved
            by the platform before model.run() is invoked.
    """

    tenant_id: str
    sport_id: str
    duckdb_conn: duckdb.DuckDBPyConnection
    data_dir: Path
    runrefs: dict[str, str] = field(default_factory=dict)

    def schema(self) -> str:
        """Tenant-scoped DuckDB schema name."""
        return f"tenant_{self.tenant_id}"

    def output_path(self, model_name: str, run_id: str) -> Path:
        """Filesystem path for a model run's Parquet output."""
        return self.data_dir / "outputs" / self.tenant_id / model_name / f"run_{run_id}.parquet"

    def write_output(
        self,
        model_name: str,
        df: pd.DataFrame,
        run_id: str,
    ) -> tuple[str, int]:
        """Persist a model run's output DataFrame as Parquet + register a DuckDB view.

        Returns: ``(dataset_name, row_count)``.
        """
        path = self.output_path(model_name, run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)

        schema = self.schema()
        view_name = f"{schema}.{model_name}_{run_id}"
        self.duckdb_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        # DuckDB does not accept prepared params inside DDL; embed the path
        # with single-quote escaping.
        escaped_path = str(path).replace("'", "''")
        self.duckdb_conn.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{escaped_path}')"
        )
        return view_name, len(df)

    def runref(self, field_name: str) -> str:
        """Resolve a config-level RunRef to a queryable DuckDB dataset name."""
        if field_name not in self.runrefs:
            raise KeyError(f"RunRef {field_name!r} not resolved on this context.")
        return self.runrefs[field_name]
