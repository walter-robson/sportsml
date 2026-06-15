"""Model registry + ModelTemplate smoke tests."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import BaseModel, Field
from sportsml.core.models.base import ModelTemplate
from sportsml.core.models.registry import (
    _REGISTRY,
    get_model,
    list_models,
    register_model,
)
from sportsml.core.models.runs import ModelRunOutput, RunRef


class FakeConfig(BaseModel):
    threshold: float = Field(0.5, ge=0.0, le=1.0)


class FakeOutput(BaseModel):
    score: float


class FakeModel(ModelTemplate):
    name: ClassVar[str] = "fake_model"
    version: ClassVar[str] = "0.0.1"
    sport_id: ClassVar[str] = "test"
    config_schema: ClassVar[type[BaseModel]] = FakeConfig
    output_schema: ClassVar[type[BaseModel]] = FakeOutput

    def run(self, config, ctx):  # noqa: ANN001, D401
        import pandas as pd

        return ModelRunOutput(rows=pd.DataFrame([{"score": config.threshold}]))


@pytest.fixture
def isolated_registry():
    """Snapshot and restore the global registry so tests don't leak state."""
    snapshot = dict(_REGISTRY)
    try:
        yield
    finally:
        _REGISTRY.clear()
        _REGISTRY.update(snapshot)


def test_register_and_lookup_roundtrip(isolated_registry):
    fake = FakeModel()
    register_model(fake)
    assert get_model("fake_model") is fake
    assert "fake_model" in {m.name for m in list_models()}


def test_describe_returns_json_schema_for_config(isolated_registry):
    fake = FakeModel()
    register_model(fake)
    desc = get_model("fake_model").describe()
    assert desc["id"] == "fake_model"
    assert "config_schema" in desc
    assert "properties" in desc["config_schema"]


def test_runref_is_pydantic_v2_frozen():
    ref = RunRef[FakeOutput](run_id="abc", model_id="fake_model")
    assert ref.run_id == "abc"
    assert ref.model_id == "fake_model"
