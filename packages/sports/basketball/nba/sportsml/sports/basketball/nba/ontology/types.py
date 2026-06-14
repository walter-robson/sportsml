"""NBA ObjectType extensions.

These types live in the sport plugin and never bleed into core. Core remains
sport-agnostic; NBA-specific concepts attach via sibling tables and FK links.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from sportsml.core.ontology.base import Link, ObjectType, Property


class Possession(ObjectType):
    """A continuous offensive possession."""

    __type_name__: ClassVar[str] = "basketball.nba.possession"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("game_id", "string"),
        Property("period", "int"),
        Property("game_clock_start", "string"),
        Property("game_clock_end", "string"),
        Property("offense_team_id", "string"),
        Property("defense_team_id", "string"),
        Property("outcome", "string"),
        Property("points_scored", "int"),
        Property("possession_seconds", "float", nullable=True),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("game", "core.game", "one"),
        Link("offense_team", "core.team", "one"),
        Link("defense_team", "core.team", "one"),
        Link("shots", "basketball.nba.shot", "many"),
    ]

    id: str
    game_id: str
    period: int
    game_clock_start: str
    game_clock_end: str
    offense_team_id: str
    defense_team_id: str
    outcome: Literal["made_fg", "missed_fg", "turnover", "foul_ft", "end_period", "other"]
    points_scored: int
    possession_seconds: float | None = None


class Shot(ObjectType):
    """A single shot attempt."""

    __type_name__: ClassVar[str] = "basketball.nba.shot"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("possession_id", "string", nullable=True),
        Property("game_id", "string"),
        Property("shooter_id", "string"),
        Property("x", "float"),
        Property("y", "float"),
        Property("distance_ft", "float"),
        Property("shot_type", "string"),
        Property("made", "bool"),
        Property("shot_value", "int"),
        Property("assisted_by_id", "string", nullable=True),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("possession", "basketball.nba.possession", "one"),
        Link("shooter", "core.player", "one"),
        Link("assist", "core.player", "one"),
    ]

    id: str
    possession_id: str | None = None
    game_id: str
    shooter_id: str
    x: float
    y: float
    distance_ft: float
    shot_type: str
    made: bool
    shot_value: int
    assisted_by_id: str | None = None


class Lineup(ObjectType):
    """A 5-man lineup (canonical sorted player_ids hash).

    ``id`` is the canonical sorted-tuple hash so identical 5-man groups
    collapse regardless of substitution order.
    """

    __type_name__: ClassVar[str] = "basketball.nba.lineup"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("team_id", "string"),
        Property("player_ids", "list[string]"),
    ]

    id: str
    team_id: str
    player_ids: list[str]


class LineupStint(ObjectType):
    """A continuous span during which a single 5-man lineup is on the floor."""

    __type_name__: ClassVar[str] = "basketball.nba.lineup_stint"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("game_id", "string"),
        Property("team_id", "string"),
        Property("lineup_id", "string"),
        Property("start_time_s", "float"),
        Property("end_time_s", "float"),
        Property("possessions_played", "int"),
        Property("points_for", "int"),
        Property("points_against", "int"),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("game", "core.game", "one"),
        Link("lineup", "basketball.nba.lineup", "one"),
    ]

    id: str
    game_id: str
    team_id: str
    lineup_id: str
    start_time_s: float
    end_time_s: float
    possessions_played: int
    points_for: int
    points_against: int


class Substitution(ObjectType):
    """One player swap event."""

    __type_name__: ClassVar[str] = "basketball.nba.substitution"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("game_id", "string"),
        Property("team_id", "string"),
        Property("period", "int"),
        Property("game_clock_s", "float"),
        Property("player_in_id", "string"),
        Property("player_out_id", "string"),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("game", "core.game", "one"),
        Link("player_in", "core.player", "one"),
        Link("player_out", "core.player", "one"),
    ]

    id: str
    game_id: str
    team_id: str
    period: int
    game_clock_s: float
    player_in_id: str
    player_out_id: str


class DraftProspect(ObjectType):
    """A draft prospect linked to a player and (optionally) tenant scouting data."""

    __type_name__: ClassVar[str] = "basketball.nba.draft_prospect"
    __properties__: ClassVar[list[Property]] = [
        Property("id", "string"),
        Property("player_id", "string"),
        Property("draft_year", "int"),
        Property("last_league_id", "string", nullable=True),
        Property("last_team_id", "string", nullable=True),
        Property("mock_position", "int", nullable=True),
        Property("scout_grade", "float", nullable=True),
    ]
    __links__: ClassVar[list[Link]] = [
        Link("player", "core.player", "one"),
    ]

    id: str
    player_id: str
    draft_year: int
    last_league_id: str | None = None
    last_team_id: str | None = None
    mock_position: int | None = None
    scout_grade: float | None = None
