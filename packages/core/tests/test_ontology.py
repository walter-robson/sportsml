"""Smoke tests for core ontology types."""

from __future__ import annotations

from datetime import date

from sportsml.core.ontology import Game, League, Player, Season, Team


def test_player_instantiates_with_required_fields():
    p = Player(id="p1", sport_id="basketball.nba", full_name="Test Player")
    assert p.full_name == "Test Player"
    assert p.position is None
    assert p.type_name() == "core.player"


def test_player_schema_dict_has_metadata():
    schema = Player.schema_dict()
    assert schema["type_name"] == "core.player"
    assert {p["name"] for p in schema["properties"]} >= {"id", "full_name"}


def test_game_links_metadata():
    schema = Game.schema_dict()
    targets = {link["target"] for link in schema["links"]}
    assert "core.team" in targets
    assert "core.season" in targets


def test_full_ontology_chain_constructs():
    league = League(id="nba", sport_id="basketball.nba", name="NBA")
    season = Season(id="2023-24", league_id=league.id, name="2023-24")
    home = Team(id="t1", league_id=league.id, name="Home")
    away = Team(id="t2", league_id=league.id, name="Away")
    game = Game(
        id="g1",
        season_id=season.id,
        date=date(2024, 1, 15),
        home_team_id=home.id,
        away_team_id=away.id,
        home_score=101,
        away_score=99,
    )
    assert game.home_team_id == "t1"
    assert game.home_score - game.away_score == 2
