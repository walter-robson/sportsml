"""Derive Shot rows from raw shot chart, joined with possessions when possible."""

import pandas as pd
from dagster import AssetExecutionContext, Output, asset
from sportsml.sports.basketball.nba.ingestion.assets import raw_nba_shot_chart
from sportsml.sports.basketball.nba.transforms._partitions import season_partitions


@asset(
    partitions_def=season_partitions,
    group_name="nba_ontology",
    compute_kind="duckdb",
    deps=[raw_nba_shot_chart],
)
def nba_shots(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Project raw shot chart into the Shot ObjectType schema."""
    from sportsml.sports.basketball.nba.ingestion import cache

    raw = cache.load_cached("raw_nba_shot_chart", context.partition_key)
    if raw is None or raw.empty:
        import pandas as pd
        return Output(pd.DataFrame(), metadata={"rows": 0})

    df = raw.rename(columns={
        "GAME_ID": "game_id",
        "PLAYER_ID": "shooter_id",
        "LOC_X": "x",
        "LOC_Y": "y",
        "SHOT_DISTANCE": "distance_ft",
        "SHOT_TYPE": "shot_type",
    }).copy()
    df["id"] = (
        df["game_id"].astype(str) + "_"
        + df["shooter_id"].astype(str) + "_"
        + raw["GAME_EVENT_ID"].astype(str)
    )
    df["made"] = raw["SHOT_MADE_FLAG"].astype(bool)
    df["shot_value"] = raw["SHOT_TYPE"].str.contains("3PT").map({True: 3, False: 2})
    df["possession_id"] = None
    df["assisted_by_id"] = None
    df = df[[
        "id", "possession_id", "game_id", "shooter_id",
        "x", "y", "distance_ft", "shot_type",
        "made", "shot_value", "assisted_by_id",
    ]]
    return Output(df, metadata={"rows": len(df)})
