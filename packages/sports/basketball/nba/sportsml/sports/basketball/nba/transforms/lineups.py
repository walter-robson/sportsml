"""Unique 5-man lineup catalog derived from stints."""

import pandas as pd
from dagster import AssetExecutionContext, Output, asset
from sportsml.sports.basketball.nba.transforms._partitions import season_partitions
from sportsml.sports.basketball.nba.transforms.lineup_stints import nba_lineup_stints


@asset(
    partitions_def=season_partitions,
    group_name="nba_ontology",
    compute_kind="duckdb",
    deps=[nba_lineup_stints],
)
def nba_lineups(context: AssetExecutionContext, nba_lineup_stints: "pd.DataFrame") -> Output[pd.DataFrame]:  # noqa: ARG001
    """One row per unique (team_id, lineup_id) seen in stints."""
    import pandas as pd

    if nba_lineup_stints is None or nba_lineup_stints.empty:
        return Output(pd.DataFrame(), metadata={"rows": 0})
    df = (
        nba_lineup_stints[["team_id", "lineup_id", "player_ids"]]
        .drop_duplicates(subset=["lineup_id"])
        .rename(columns={"lineup_id": "id"})
        .reset_index(drop=True)
    )
    df["id_full"] = df["id"]
    return Output(df, metadata={"rows": len(df)})
