"""Model run lifecycle types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound=BaseModel)


class ModelRunStatus(StrEnum):
    """Run status values mirrored in the v0 SQLite runs table."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(slots=True)
class ModelRun:
    """Bookkeeping record persisted to the runs DB.

    Mirrors the spec's Postgres ``model_runs`` table; v0 stores it in SQLite.
    """

    run_id: str
    model_id: str
    tenant_id: str
    config_hash: str
    config_json: str
    status: ModelRunStatus
    started_at: datetime
    finished_at: datetime | None = None
    duration_s: float | None = None
    row_count: int | None = None
    output_dataset: str | None = None
    error: str | None = None
    label: str | None = None


@dataclass(slots=True)
class ModelRunOutput:
    """Structured output of a model run.

    Holds the in-memory DataFrame returned by ``ModelTemplate.run`` and a
    pointer to its persisted location once written. Use ``ctx.write_output``
    to materialize ``rows`` and populate ``dataset`` and ``row_count``.
    """

    rows: object  # pandas.DataFrame at runtime; kept untyped to avoid hard dep here
    dataset: str | None = None
    row_count: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)


class RunRef(BaseModel, Generic[T]):  # noqa: UP046 — Pydantic generics + PEP 695 not yet smooth
    """Typed reference to a prior model run, usable inside another model's config.

    The platform resolves a ``RunRef[X]`` by looking up the referenced run's
    output dataset and exposing it to the dependent model via ``ctx.runref``.
    v0 ships the primitive; no cross-app UI exercises it yet.
    """

    model_config = ConfigDict(frozen=True)

    run_id: str
    model_id: str
