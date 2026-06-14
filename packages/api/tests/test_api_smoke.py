"""End-to-end smoke for the FastAPI service.

We construct an isolated app instance per test pointed at a temp data dir so
the suite is hermetic.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Build a TestClient with an isolated temp data dir + duckdb."""
    with TemporaryDirectory() as tmp:
        os.environ["SPORTSML_DATA_DIR"] = tmp
        os.environ["SPORTSML_DUCKDB_PATH"] = str(Path(tmp) / "test.duckdb")
        os.environ["SPORTSML_TENANT_ID"] = "demo"
        # Import inside fixture so env vars apply before the app builds settings.
        from sportsml_api.main import create_app

        app = create_app()
        with TestClient(app) as c:
            yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_models_includes_lineup_net_rating(client):
    r = client.get("/models")
    assert r.status_code == 200
    ids = {m["id"] for m in r.json()["models"]}
    assert "lineup_net_rating" in ids


def test_model_schema_has_expected_knobs(client):
    r = client.get("/models/lineup_net_rating/schema")
    assert r.status_code == 200
    schema = r.json()
    props = set(schema["properties"].keys())
    assert {"min_possessions", "rapm_lambda", "three_point_emphasis"}.issubset(props)


def test_list_apps_includes_lineup_analysis(client):
    r = client.get("/apps")
    assert r.status_code == 200
    ids = {a["id"] for a in r.json()["apps"]}
    assert "lineup_analysis" in ids


def test_ontology_types_lists_core_and_nba_types(client):
    r = client.get("/ontology/types")
    assert r.status_code == 200
    names = {t["type_name"] for t in r.json()["types"]}
    assert "core.player" in names
    assert "basketball.nba.lineup" in names


def test_run_model_with_invalid_config_returns_422(client):
    r = client.post(
        "/models/lineup_net_rating/runs",
        json={"config": {"rapm_lambda": -10}},  # below ge=10
    )
    assert r.status_code == 422
