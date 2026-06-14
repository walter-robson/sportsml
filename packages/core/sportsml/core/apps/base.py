"""App ABC + declarative layout schema.

An App declares which model templates it uses and a panel layout. The
Workbench shell is generic — it renders whatever an App emits without any
sport-aware code.
"""

from __future__ import annotations

from abc import ABC
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AppPanel(BaseModel):
    """One renderable panel in an App layout."""

    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["config", "table", "chart", "heatmap", "detail"]
    title: str
    # JSON-serializable hints; the Workbench interprets them per ``kind``.
    options: dict[str, object] = {}


class AppLayout(BaseModel):
    """Top-level layout: ordered panels grouped into ``left`` (config) and ``main`` (results)."""

    model_config = ConfigDict(extra="forbid")

    left: list[AppPanel] = []
    main: list[AppPanel] = []


class App(ABC):
    """Abstract App descriptor.

    Concrete subclasses set the class attributes and are registered via
    ``sportsml.core.apps.registry.register_app``.
    """

    id: str
    sport_id: str
    name: str
    description: str
    models_used: list[str]
    layout: AppLayout

    def describe(self) -> dict[str, object]:
        return {
            "id": self.id,
            "sport_id": self.sport_id,
            "name": self.name,
            "description": self.description,
            "models_used": self.models_used,
            "layout": self.layout.model_dump(),
        }
