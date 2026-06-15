"""Postgres-backed run persistence.

The previous v0 stored runs in a local SQLite file; this layer is the same
schema shape on Postgres (Supabase in production). Function signatures are
unchanged so routers do not need updates.

Tenants are addressed by slug (e.g. ``"demo"``) at the API boundary and
translated to UUIDs internally via the :class:`Tenant` lookup table.
"""

from __future__ import annotations

import hashlib
import json
import uuid

from sportsml.core.models.runs import ModelRun, ModelRunStatus
from sqlalchemy import select
from sqlalchemy.orm import Session

from sportsml_api.db import Base, ModelRunRow, Tenant, get_engine
from sportsml_api.db.session import session_scope

DEMO_TENANT_SLUG = "demo"
DEMO_TENANT_NAME = "Demo Tenant"


def init_runs_db() -> None:
    """Create all tables and seed the bootstrap demo tenant.

    Idempotent — safe to call on every API startup. Real schema evolution
    flows through Alembic migrations (``alembic upgrade head``).
    """
    engine = get_engine()
    Base.metadata.create_all(engine)
    _ensure_demo_tenant()


def _ensure_demo_tenant() -> Tenant:
    with session_scope() as s:
        t = s.scalar(select(Tenant).where(Tenant.slug == DEMO_TENANT_SLUG))
        if t is None:
            t = Tenant(slug=DEMO_TENANT_SLUG, name=DEMO_TENANT_NAME)
            s.add(t)
            s.flush()
        return t


def _resolve_tenant_id(session: Session, slug: str) -> uuid.UUID:
    t = session.scalar(select(Tenant).where(Tenant.slug == slug))
    if t is None:
        raise ValueError(f"unknown tenant slug: {slug!r}")
    return t.id


def _to_row(run: ModelRun, tenant_uuid: uuid.UUID) -> ModelRunRow:
    return ModelRunRow(
        run_id=run.run_id,
        tenant_id=tenant_uuid,
        model_id=run.model_id,
        config_hash=run.config_hash,
        config_json=json.loads(run.config_json),
        status=run.status.value,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_s=run.duration_s,
        row_count=run.row_count,
        output_dataset=run.output_dataset,
        error=run.error,
        label=run.label,
    )


def _from_row(row: ModelRunRow, tenant_slug: str) -> ModelRun:
    return ModelRun(
        run_id=row.run_id,
        model_id=row.model_id,
        tenant_id=tenant_slug,
        config_hash=row.config_hash,
        config_json=json.dumps(row.config_json, sort_keys=True),
        status=ModelRunStatus(row.status),
        started_at=row.started_at,
        finished_at=row.finished_at,
        duration_s=row.duration_s,
        row_count=row.row_count,
        output_dataset=row.output_dataset,
        error=row.error,
        label=row.label,
    )


def insert_run(run: ModelRun) -> None:
    with session_scope() as s:
        tenant_uuid = _resolve_tenant_id(s, run.tenant_id)
        s.add(_to_row(run, tenant_uuid))


def update_run(run: ModelRun) -> None:
    with session_scope() as s:
        row = s.get(ModelRunRow, run.run_id)
        if row is None:
            raise ValueError(f"unknown run_id: {run.run_id!r}")
        row.status = run.status.value
        row.finished_at = run.finished_at
        row.duration_s = run.duration_s
        row.row_count = run.row_count
        row.output_dataset = run.output_dataset
        row.error = run.error


def get_run(run_id: str) -> ModelRun | None:
    with session_scope() as s:
        row = s.get(ModelRunRow, run_id)
        if row is None:
            return None
        return _from_row(row, row.tenant.slug)


def find_run_by_hash(model_id: str, tenant_id: str, config_hash: str) -> ModelRun | None:
    """Return the most recent succeeded run for a config_hash within the tenant."""
    with session_scope() as s:
        tenant_uuid = _resolve_tenant_id(s, tenant_id)
        row = s.scalar(
            select(ModelRunRow)
            .where(
                ModelRunRow.tenant_id == tenant_uuid,
                ModelRunRow.model_id == model_id,
                ModelRunRow.config_hash == config_hash,
                ModelRunRow.status == ModelRunStatus.SUCCEEDED.value,
            )
            .order_by(ModelRunRow.started_at.desc())
            .limit(1)
        )
        if row is None:
            return None
        return _from_row(row, tenant_id)


def compute_config_hash(model_id: str, config: dict) -> str:
    """Stable hash over (model_id, canonical-JSON of config) for caching."""
    payload = json.dumps({"model_id": model_id, "config": config}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
