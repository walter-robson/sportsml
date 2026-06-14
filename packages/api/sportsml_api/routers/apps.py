"""App routes: list registered apps + return layout."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sportsml.core.apps.registry import get_app, list_apps

router = APIRouter()


@router.get("")
def list_all_apps() -> dict[str, object]:
    return {"apps": [a.describe() for a in list_apps()]}


@router.get("/{app_id}")
def get_app_meta(app_id: str) -> dict[str, object]:
    try:
        return get_app(app_id).describe()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
