"""Thin wrapper around ``nba_api`` endpoints with rate-limiting + retries.

We intentionally don't import ``nba_api`` at module top-level so test
collection doesn't pull the network-bound dependency tree. The wrapper is
lazy and only constructs endpoint instances when called.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from sportsml.sports.basketball.nba.ingestion.config import ingestion_config
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    import pandas as pd


_LAST_CALL_AT: float = 0.0


def _throttle() -> None:
    """Sleep so consecutive endpoint calls are at least ``api_delay_s`` apart."""
    global _LAST_CALL_AT  # noqa: PLW0603 — single-module mutable, simpler than a class
    cfg = ingestion_config()
    now = time.monotonic()
    delta = now - _LAST_CALL_AT
    if delta < cfg.api_delay_s:
        time.sleep(cfg.api_delay_s - delta)
    _LAST_CALL_AT = time.monotonic()


def _retry_decorator():  # noqa: ANN202 — tenacity-built decorator, type is dynamic
    cfg = ingestion_config()
    return retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(cfg.api_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )


@_retry_decorator()
def league_game_finder(season: str) -> pd.DataFrame:
    """Fetch all games in a season from LeagueGameFinder."""
    from nba_api.stats.endpoints import leaguegamefinder

    _throttle()
    cfg = ingestion_config()
    resp = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        league_id_nullable="00",
        season_type_nullable="Regular Season",
        timeout=cfg.api_timeout,
    )
    return resp.get_data_frames()[0]


@_retry_decorator()
def play_by_play(game_id: str) -> pd.DataFrame:
    from nba_api.stats.endpoints import playbyplayv2

    _throttle()
    cfg = ingestion_config()
    resp = playbyplayv2.PlayByPlayV2(game_id=game_id, timeout=cfg.api_timeout)
    return resp.get_data_frames()[0]


@_retry_decorator()
def box_score(game_id: str) -> pd.DataFrame:
    from nba_api.stats.endpoints import boxscoretraditionalv2

    _throttle()
    cfg = ingestion_config()
    resp = boxscoretraditionalv2.BoxScoreTraditionalV2(
        game_id=game_id, timeout=cfg.api_timeout
    )
    return resp.get_data_frames()[0]


@_retry_decorator()
def shot_chart(team_id: int, season: str) -> pd.DataFrame:
    from nba_api.stats.endpoints import shotchartdetail

    _throttle()
    cfg = ingestion_config()
    resp = shotchartdetail.ShotChartDetail(
        team_id=team_id,
        player_id=0,
        season_nullable=season,
        season_type_all_star="Regular Season",
        context_measure_simple="FGA",
        timeout=cfg.api_timeout,
    )
    return resp.get_data_frames()[0]


@_retry_decorator()
def team_roster(team_id: int, season: str) -> pd.DataFrame:
    from nba_api.stats.endpoints import commonteamroster

    _throttle()
    cfg = ingestion_config()
    resp = commonteamroster.CommonTeamRoster(
        team_id=team_id, season=season, timeout=cfg.api_timeout
    )
    return resp.get_data_frames()[0]


@_retry_decorator()
def all_players(season: str) -> pd.DataFrame:
    from nba_api.stats.endpoints import commonallplayers

    _throttle()
    cfg = ingestion_config()
    resp = commonallplayers.CommonAllPlayers(
        is_only_current_season=0, season=season, timeout=cfg.api_timeout
    )
    return resp.get_data_frames()[0]


@_retry_decorator()
def team_info(team_id: int, season: str) -> pd.DataFrame:
    from nba_api.stats.endpoints import teaminfocommon

    _throttle()
    cfg = ingestion_config()
    resp = teaminfocommon.TeamInfoCommon(
        team_id=team_id, season_nullable=season, timeout=cfg.api_timeout
    )
    return resp.get_data_frames()[0]
