"""Per-player season aggregates from box scores."""

import pandas as pd
from dagster import AssetExecutionContext, Output, asset
from sportsml.sports.basketball.nba.ingestion.assets import raw_nba_box_scores
from sportsml.sports.basketball.nba.transforms._partitions import season_partitions


@asset(
    partitions_def=season_partitions,
    group_name="nba_features",
    compute_kind="duckdb",
    deps=[raw_nba_box_scores],
)
def nba_player_season_stats(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Aggregate raw box scores by (player_id, season)."""
    import pandas as pd
    from sportsml.sports.basketball.nba.ingestion import cache

    box = cache.load_cached("raw_nba_box_scores", context.partition_key)
    if box is None or box.empty:
        return Output(pd.DataFrame(), metadata={"rows": 0})

    numeric = ["PTS", "AST", "REB", "STL", "BLK", "TO", "FGM", "FGA", "FG3M", "FG3A"]
    available = [c for c in numeric if c in box.columns]
    df = (
        box.groupby(["PLAYER_ID", "PLAYER_NAME"], dropna=False)[available]
        .sum(min_count=1)
        .reset_index()
        .rename(columns={"PLAYER_ID": "player_id", "PLAYER_NAME": "player_name"})
    )
    df["season"] = context.partition_key
    return Output(df, metadata={"rows": len(df)})
