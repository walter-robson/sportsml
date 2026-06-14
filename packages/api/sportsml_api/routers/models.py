"""Model routes: list, schema, submit run, fetch run, fetch output."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, ValidationError
from sportsml.core.models.context import TenantContext
from sportsml.core.models.registry import get_model, list_models
from sportsml.core.models.runs import ModelRun, ModelRunStatus

from sportsml_api.deps import get_tenant_context
from sportsml_api.persistence import (
    compute_config_hash,
    find_run_by_hash,
    get_run,
    insert_run,
    update_run,
)

router = APIRouter()


class RunRequest(BaseModel):
    """Body of POST /models/{id}/runs."""

    model_config = ConfigDict(extra="forbid")

    config: dict[str, Any]
    label: str | None = None


@router.get("")
def list_all_models() -> dict[str, object]:
    return {"models": [m.describe() for m in list_models()]}


@router.get("/{model_id}")
def get_model_meta(model_id: str) -> dict[str, object]:
    try:
        return get_model(model_id).describe()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{model_id}/schema")
def get_model_schema(model_id: str) -> dict[str, object]:
    try:
        m = get_model(model_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return m.config_schema.model_json_schema()


@router.post("/{model_id}/runs", status_code=202)
def submit_run(
    model_id: str,
    body: RunRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> dict[str, object]:
    try:
        template = get_model(model_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    try:
        config = template.config_schema(**body.config)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=json.loads(e.json())) from e

    config_dict = config.model_dump()
    config_hash = compute_config_hash(model_id, config_dict)

    cached = find_run_by_hash(model_id, ctx.tenant_id, config_hash)
    if cached:
        return {
            "run_id": cached.run_id,
            "status": cached.status.value,
            "cached": True,
        }

    run_id = uuid.uuid4().hex
    started = datetime.utcnow()
    run = ModelRun(
        run_id=run_id,
        model_id=model_id,
        tenant_id=ctx.tenant_id,
        config_hash=config_hash,
        config_json=json.dumps(config_dict),
        status=ModelRunStatus.RUNNING,
        started_at=started,
        label=body.label,
    )
    insert_run(run)

    try:
        output = template.run(config, ctx)
        df = output.rows
        dataset_name, row_count = ctx.write_output(model_id, df, run_id)
        finished = datetime.utcnow()
        run.status = ModelRunStatus.SUCCEEDED
        run.finished_at = finished
        run.duration_s = (finished - started).total_seconds()
        run.row_count = row_count
        run.output_dataset = dataset_name
        update_run(run)
    except Exception as e:  # noqa: BLE001 — convert any model error into a persisted failure
        finished = datetime.utcnow()
        run.status = ModelRunStatus.FAILED
        run.finished_at = finished
        run.duration_s = (finished - started).total_seconds()
        run.error = str(e)
        update_run(run)
        raise HTTPException(status_code=500, detail=f"Model run failed: {e}") from e

    return {
        "run_id": run_id,
        "status": run.status.value,
        "duration_s": run.duration_s,
        "row_count": run.row_count,
        "output_dataset": run.output_dataset,
    }


@router.get("/{model_id}/runs/{run_id}")
def get_run_status(model_id: str, run_id: str) -> dict[str, object]:
    run = get_run(run_id)
    if run is None or run.model_id != model_id:
        raise HTTPException(status_code=404, detail="Run not found.")
    return {
        "run_id": run.run_id,
        "model_id": run.model_id,
        "tenant_id": run.tenant_id,
        "status": run.status.value,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "duration_s": run.duration_s,
        "row_count": run.row_count,
        "output_dataset": run.output_dataset,
        "label": run.label,
        "error": run.error,
    }


@router.get("/{model_id}/runs/{run_id}/output")
def get_run_output(
    model_id: str,
    run_id: str,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    sort: str | None = Query(None, description="Column name; prefix with '-' for descending."),
) -> dict[str, object]:
    run = get_run(run_id)
    if run is None or run.model_id != model_id:
        raise HTTPException(status_code=404, detail="Run not found.")
    path = ctx.output_path(model_id, run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run output not materialized.")
    order = ""
    if sort:
        col = sort.lstrip("-")
        direction = "DESC" if sort.startswith("-") else "ASC"
        order = f" ORDER BY {col} {direction}"
    escaped_path = str(path).replace("'", "''")
    df = ctx.duckdb_conn.execute(
        f"SELECT * FROM read_parquet('{escaped_path}'){order} LIMIT ? OFFSET ?",
        [limit, offset],
    ).df()
    # Coerce numpy arrays (DuckDB LIST columns surface as ndarray) to lists
    # so Pydantic / orjson can serialize the response.
    rows = [
        {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in r.items()}
        for r in df.to_dict("records")
    ]
    return {"run_id": run_id, "limit": limit, "offset": offset, "rows": rows}
