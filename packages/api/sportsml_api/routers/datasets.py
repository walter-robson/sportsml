"""Datasets routes: list materialized assets + paged samples."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sportsml.core.models.context import TenantContext

from sportsml_api.deps import get_tenant_context

router = APIRouter()


def _scan_datasets(data_dir: Path) -> list[dict[str, object]]:
    """Walk ``data/`` for Parquet files and surface them as dataset entries."""
    out: list[dict[str, object]] = []
    if not data_dir.exists():
        return out
    for p in sorted(data_dir.rglob("*.parquet")):
        rel = p.relative_to(data_dir)
        out.append(
            {
                "id": str(rel),
                "path": str(p),
                "size_bytes": p.stat().st_size,
                "name": p.stem,
            }
        )
    return out


@router.get("")
def list_datasets(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> dict[str, object]:
    return {"datasets": _scan_datasets(ctx.data_dir)}


@router.get("/{dataset_id:path}/sample")
def sample_dataset(
    dataset_id: str,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    full = (ctx.data_dir / dataset_id).resolve()
    # Path traversal guard: refuse anything outside data_dir.
    if not str(full).startswith(str(ctx.data_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid dataset path.")
    if not full.exists():
        raise HTTPException(status_code=404, detail=f"No dataset at {dataset_id!r}.")
    df = ctx.duckdb_conn.execute(
        "SELECT * FROM read_parquet(?) LIMIT ? OFFSET ?",
        [str(full), limit, offset],
    ).df()
    return {
        "dataset_id": dataset_id,
        "limit": limit,
        "offset": offset,
        "rows": df.to_dict("records"),
    }
