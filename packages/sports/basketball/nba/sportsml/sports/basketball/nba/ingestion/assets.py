"""Dagster source assets for NBA raw data.

Each asset returns a pandas DataFrame; the dagster-duckdb IO manager persists
it under a Hive-partitioned path. Smoke mode caps games to ``SMOKE_GAME_LIMIT``
for fast demos; full mode pulls the entire season.

Note: this module intentionally does NOT use ``from __future__ import annotations``.
Dagster's ``@asset`` decorator evaluates return-type annotations at decoration
time via ``get_type_hints``, which doesn't tolerate string-only forward refs.
"""

import pandas as pd
from dagster import (
    AssetExecutionContext,
    Output,
    StaticPartitionsDefinition,
    asset,
)
from sportsml.sports.basketball.nba.ingestion import cache, client
from sportsml.sports.basketball.nba.ingestion.config import (
    SEASON_V0,
    SMOKE_DATE_FROM,
    SMOKE_DATE_TO,
    SMOKE_GAME_LIMIT,
    IngestionMode,
    ingestion_config,
)

season_partitions = StaticPartitionsDefinition([SEASON_V0])


def _cached_or_fetch(asset_name: str, key: str, fetch_fn) -> "pd.DataFrame":  # noqa: ANN001
    cached = cache.load_cached(asset_name, key)
    if cached is not None:
        return cached
    df = fetch_fn()
    cache.save_cached(asset_name, key, df)
    return df


@asset(partitions_def=season_partitions, group_name="nba_raw", compute_kind="nba_api")
def raw_nba_games(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """All regular-season games for the partition season."""
    season = context.partition_key
    df = _cached_or_fetch("raw_nba_games", season, lambda: client.league_game_finder(season))
    cfg = ingestion_config()
    if cfg.mode is IngestionMode.SMOKE:
        df = df[(df["GAME_DATE"] >= SMOKE_DATE_FROM) & (df["GAME_DATE"] <= SMOKE_DATE_TO)]
        df = df.drop_duplicates(subset=["GAME_ID"]).head(SMOKE_GAME_LIMIT * 2)
    return Output(df, metadata={"rows": len(df), "mode": cfg.mode.value})


@asset(
    partitions_def=season_partitions,
    group_name="nba_raw",
    compute_kind="nba_api",
    deps=[raw_nba_games],
)
def raw_nba_pbp(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Play-by-play events for each game in ``raw_nba_games``."""
    import pandas as pd

    games = cache.load_cached("raw_nba_games", context.partition_key)
    if games is None:
        raise RuntimeError("raw_nba_games not yet materialized.")
    game_ids = sorted(games["GAME_ID"].astype(str).unique())[:SMOKE_GAME_LIMIT]
    frames = [
        _cached_or_fetch("raw_nba_pbp", gid, lambda gid=gid: client.play_by_play(gid))
        for gid in game_ids
    ]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return Output(df, metadata={"rows": len(df), "games": len(game_ids)})


@asset(
    partitions_def=season_partitions,
    group_name="nba_raw",
    compute_kind="nba_api",
    deps=[raw_nba_games],
)
def raw_nba_box_scores(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Traditional box scores for each game."""
    import pandas as pd

    games = cache.load_cached("raw_nba_games", context.partition_key)
    if games is None:
        raise RuntimeError("raw_nba_games not yet materialized.")
    game_ids = sorted(games["GAME_ID"].astype(str).unique())[:SMOKE_GAME_LIMIT]
    frames = [
        _cached_or_fetch("raw_nba_box_scores", gid, lambda gid=gid: client.box_score(gid))
        for gid in game_ids
    ]
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return Output(df, metadata={"rows": len(df), "games": len(game_ids)})


@asset(partitions_def=season_partitions, group_name="nba_raw", compute_kind="nba_api")
def raw_nba_teams(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """League-wide team list. nba_api ships a static teams table; we use it
    to avoid 30 separate API calls when we only need ids/names."""
    import pandas as pd
    from nba_api.stats.static import teams as static_teams

    df = pd.DataFrame(static_teams.get_teams())
    cache.save_cached("raw_nba_teams", context.partition_key, df)
    return Output(df, metadata={"rows": len(df)})


@asset(partitions_def=season_partitions, group_name="nba_raw", compute_kind="nba_api")
def raw_nba_players(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """League-wide players for the season."""
    season = context.partition_key
    df = _cached_or_fetch("raw_nba_players", season, lambda: client.all_players(season))
    return Output(df, metadata={"rows": len(df)})


@asset(
    partitions_def=season_partitions,
    group_name="nba_raw",
    compute_kind="nba_api",
    deps=[raw_nba_teams],
)
def raw_nba_team_roster(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Team rosters for the season. Iterates all 30 teams."""
    import pandas as pd

    teams = cache.load_cached("raw_nba_teams", context.partition_key)
    if teams is None:
        raise RuntimeError("raw_nba_teams not yet materialized.")
    season = context.partition_key
    frames = []
    for tid in teams["id"].astype(int).tolist():
        key = f"{tid}_{season}"
        frames.append(
            _cached_or_fetch(
                "raw_nba_team_roster", key, lambda tid=tid: client.team_roster(tid, season)
            )
        )
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return Output(df, metadata={"rows": len(df)})


@asset(
    partitions_def=season_partitions,
    group_name="nba_raw",
    compute_kind="nba_api",
    deps=[raw_nba_teams],
)
def raw_nba_shot_chart(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Shot-chart-level detail for every team in the season."""
    import pandas as pd

    teams = cache.load_cached("raw_nba_teams", context.partition_key)
    if teams is None:
        raise RuntimeError("raw_nba_teams not yet materialized.")
    season = context.partition_key
    frames = []
    for tid in teams["id"].astype(int).tolist():
        key = f"{tid}_{season}"
        frames.append(
            _cached_or_fetch(
                "raw_nba_shot_chart", key, lambda tid=tid: client.shot_chart(tid, season)
            )
        )
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return Output(df, metadata={"rows": len(df)})


nba_source_assets = [
    raw_nba_games,
    raw_nba_pbp,
    raw_nba_box_scores,
    raw_nba_teams,
    raw_nba_players,
    raw_nba_team_roster,
    raw_nba_shot_chart,
]
