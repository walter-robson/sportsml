"""Ontology routes.

Lists registered ObjectTypes and fetches instances. v0 returns schemas only;
instance lookup falls back to DuckDB tables matching the type's lowercase
short name (best-effort).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sportsml.core.ontology.base import ObjectType
from sportsml.core.ontology.types import Game, League, Player, PlayerGame, Season, Team

from sportsml_api.deps import get_tenant_context

router = APIRouter()


def _core_types() -> list[type[ObjectType]]:
    return [League, Season, Team, Player, Game, PlayerGame]


def _nba_types() -> list[type[ObjectType]]:
    from sportsml.sports.basketball.nba.ontology.types import (
        DraftProspect,
        Lineup,
        LineupStint,
        Possession,
        Shot,
        Substitution,
    )

    return [Possession, Shot, Lineup, LineupStint, Substitution, DraftProspect]


def _all_types() -> list[type[ObjectType]]:
    return _core_types() + _nba_types()


@router.get("/types")
def list_types() -> dict[str, object]:
    return {"types": [t.schema_dict() for t in _all_types()]}


@router.get("/{type_name}/{instance_id}")
def get_instance(
    type_name: str,
    instance_id: str,
    ctx: Annotated[object, Depends(get_tenant_context)],
) -> dict[str, object]:
    """Best-effort instance lookup.

    v0 attempts to resolve ``{type_name}`` to a DuckDB table by stripping the
    common namespace prefix. Returns 404 if no such table exists in DuckDB.
    """
    matches = [t for t in _all_types() if t.type_name() == type_name]
    if not matches:
        raise HTTPException(status_code=404, detail=f"Unknown type {type_name!r}.")
    table_short = type_name.split(".")[-1]
    try:
        df = ctx.duckdb_conn.execute(  # type: ignore[attr-defined]
            f"SELECT * FROM {table_short} WHERE id = ? LIMIT 1",
            [instance_id],
        ).df()
    except Exception as e:  # noqa: BLE001 — DuckDB raises generic on missing tables
        raise HTTPException(
            status_code=404, detail=f"Could not resolve {type_name!r}: {e}"
        ) from e
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No instance with id {instance_id!r}.")
    return {"type": type_name, "instance": df.iloc[0].to_dict()}
