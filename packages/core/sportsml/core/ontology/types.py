"""Core (sport-agnostic) ObjectTypes.

These six types form the platform-wide minimal ontology. Sport plugins add
properties via sibling tables joined on the appropriate keys — they never
mutate these core types.
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from sportsml.core.ontology.base import Link, ObjectType, Property


class League(ObjectType):
    """A top-level competition (e.g. NBA, NCAA-D1)."""

    __type_name__: ClassVar[str] = "core.league"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("sport_id", "string"),
        Property("name", "string"),
        Property("country", "string", nullable=True),
        Property("level", "string", nullable=True),
    ]

    id: str
    sport_id: str
    name: str
    country: str | None = None
    level: str | None = None


class Season(ObjectType):
    """A single season within a league (e.g. NBA 2023-24)."""

    __type_name__: ClassVar[str] = "core.season"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("league_id", "string"),
        Property("name", "string"),
        Property("start_date", "date", nullable=True),
        Property("end_date", "date", nullable=True),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("league", "core.league", "one"),
    ]

    id: str
    league_id: str
    name: str
    start_date: date | None = None
    end_date: date | None = None


class Team(ObjectType):
    """A franchise / club."""

    __type_name__: ClassVar[str] = "core.team"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("league_id", "string"),
        Property("name", "string"),
        Property("abbreviation", "string", nullable=True),
        Property("city", "string", nullable=True),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("league", "core.league", "one"),
    ]

    id: str
    league_id: str
    name: str
    abbreviation: str | None = None
    city: str | None = None


class Player(ObjectType):
    """A player.

    ``position`` is a free-form string; convention is sport-specific
    (NBA: PG/SG/SF/PF/C; NFL: QB/RB/WR/...). No schema change to add a sport.
    """

    __type_name__: ClassVar[str] = "core.player"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("sport_id", "string"),
        Property("full_name", "string"),
        Property("birth_date", "date", nullable=True),
        Property("height_cm", "float", nullable=True),
        Property("weight_kg", "float", nullable=True),
        Property("position", "string", nullable=True),
    ]

    id: str
    sport_id: str
    full_name: str
    birth_date: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    position: str | None = None


class Game(ObjectType):
    """A single game / match."""

    __type_name__: ClassVar[str] = "core.game"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("season_id", "string"),
        Property("date", "date"),
        Property("home_team_id", "string"),
        Property("away_team_id", "string"),
        Property("home_score", "int", nullable=True),
        Property("away_score", "int", nullable=True),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("season", "core.season", "one"),
        Link("home_team", "core.team", "one"),
        Link("away_team", "core.team", "one"),
    ]

    id: str
    season_id: str
    date: date
    home_team_id: str
    away_team_id: str
    home_score: int | None = None
    away_score: int | None = None


class PlayerGame(ObjectType):
    """Minimal per-player per-game line.

    Sport plugins extend via sibling tables (e.g. ``basketball.nba.player_game_box``)
    joined on ``(player_id, game_id)``. Core remains stable.
    """

    __type_name__: ClassVar[str] = "core.player_game"
    __properties__: ClassVar[list[Property]] = [
        Property("player_id", "string"),
        Property("game_id", "string"),
        Property("minutes", "float", nullable=True),
        Property("plus_minus", "float", nullable=True),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("player", "core.player", "one"),
        Link("game", "core.game", "one"),
    ]

    player_id: str
    game_id: str
    minutes: float | None = None
    plus_minus: float | None = None
