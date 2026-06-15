"""Unit tests for the Postgres-backed run store.

Uses an in-memory SQLite engine so the suite is hermetic. The ORM models are
dialect-portable; the same code paths run against Postgres in deployment.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sportsml.core.models.runs import ModelRun, ModelRunStatus
from sportsml_api.db.engine import dispose_engine, init_engine
from sportsml_api.persistence import (
    compute_config_hash,
    find_run_by_hash,
    get_run,
    init_runs_db,
    insert_run,
    update_run,
)


@pytest.fixture(autouse=True)
def _isolated_db():
    init_engine("sqlite:///:memory:")
    init_runs_db()
    yield
    dispose_engine()


def _make_run(
    run_id: str = "run-1",
    *,
    config: dict | None = None,
    status: ModelRunStatus = ModelRunStatus.PENDING,
) -> ModelRun:
    cfg = config or {"rapm_lambda": 50}
    return ModelRun(
        run_id=run_id,
        model_id="lineup_net_rating",
        tenant_id="demo",
        config_hash=compute_config_hash("lineup_net_rating", cfg),
        config_json=json.dumps(cfg, sort_keys=True),
        status=status,
        started_at=datetime.now(UTC),
    )


def test_insert_and_get_roundtrip():
    run = _make_run()
    insert_run(run)
    fetched = get_run(run.run_id)
    assert fetched is not None
    assert fetched.run_id == run.run_id
    assert fetched.tenant_id == "demo"
    assert fetched.status is ModelRunStatus.PENDING
    assert fetched.model_id == "lineup_net_rating"


def test_get_missing_returns_none():
    assert get_run("does-not-exist") is None


def test_update_run_transitions_status_and_metrics():
    run = _make_run()
    insert_run(run)
    run.status = ModelRunStatus.SUCCEEDED
    run.finished_at = datetime.now(UTC)
    run.duration_s = 12.5
    run.row_count = 100
    update_run(run)
    fetched = get_run(run.run_id)
    assert fetched is not None
    assert fetched.status is ModelRunStatus.SUCCEEDED
    assert fetched.duration_s == 12.5
    assert fetched.row_count == 100


def test_find_run_by_hash_returns_latest_succeeded_only():
    cfg = {"rapm_lambda": 100}
    h = compute_config_hash("lineup_net_rating", cfg)
    # Two runs with the same config; first failed, second succeeded.
    failed = _make_run("run-fail", config=cfg, status=ModelRunStatus.FAILED)
    succeeded = _make_run("run-ok", config=cfg, status=ModelRunStatus.SUCCEEDED)
    insert_run(failed)
    insert_run(succeeded)
    found = find_run_by_hash("lineup_net_rating", "demo", h)
    assert found is not None
    assert found.run_id == "run-ok"


def test_find_run_by_hash_unknown_returns_none():
    assert find_run_by_hash("lineup_net_rating", "demo", "abc") is None


def test_find_run_by_hash_unknown_tenant_raises():
    with pytest.raises(ValueError, match="unknown tenant slug"):
        find_run_by_hash("lineup_net_rating", "not-a-tenant", "abc")


def test_compute_config_hash_is_stable_and_order_independent():
    a = compute_config_hash("m", {"x": 1, "y": 2})
    b = compute_config_hash("m", {"y": 2, "x": 1})
    assert a == b


def test_compute_config_hash_distinguishes_models():
    cfg = {"x": 1}
    assert compute_config_hash("a", cfg) != compute_config_hash("b", cfg)
