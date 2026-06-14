"""Ontology base classes and core ObjectTypes."""

from __future__ import annotations

from sportsml.core.ontology.base import Link, ObjectType, Property
from sportsml.core.ontology.types import (
    Game,
    League,
    Player,
    PlayerGame,
    Season,
    Team,
)

__all__ = [
    "Game",
    "League",
    "Link",
    "ObjectType",
    "Player",
    "PlayerGame",
    "Property",
    "Season",
    "Team",
]
