"""Filter raw PBP for substitution events.

Pure function ``extract_substitutions`` is the testable seam; the Dagster
asset just orchestrates I/O.
"""

import pandas as pd
from dagster import AssetExecutionContext, Output, asset
from sportsml.sports.basketball.nba.ingestion.assets import raw_nba_pbp
from sportsml.sports.basketball.nba.transforms._partitions import season_partitions

EVENT_SUBSTITUTION = 8


def _clock_to_seconds(clock: str) -> float:
    """Convert ``MM:SS`` PBP clock string to seconds remaining in period."""
    if not clock or ":" not in clock:
        return 0.0
    mm, ss = clock.split(":")
    return float(mm) * 60.0 + float(ss)


def extract_substitutions(pbp: "pd.DataFrame") -> "pd.DataFrame":
    """Return one row per substitution event, normalized."""
    import pandas as pd

    cols = [
        "id", "game_id", "team_id", "period",
        "game_clock_s", "player_in_id", "player_out_id",
    ]
    if pbp.empty:
        return pd.DataFrame(columns=cols)

    subs = pbp[pbp["EVENTMSGTYPE"] == EVENT_SUBSTITUTION].copy()
    if subs.empty:
        return pd.DataFrame(columns=cols)

    rows: list[dict[str, object]] = []
    for _, ev in subs.iterrows():
        team = ev.get("PLAYER1_TEAM_ID")
        if pd.isna(team):
            continue
        rows.append({
            "id": f"{ev['GAME_ID']}_{ev['EVENTNUM']}",
            "game_id": str(ev["GAME_ID"]),
            "team_id": str(int(team)),
            "period": int(ev["PERIOD"]),
            "game_clock_s": _clock_to_seconds(str(ev.get("PCTIMESTRING", "0:00"))),
            "player_out_id": str(int(ev["PLAYER1_ID"])) if pd.notna(ev.get("PLAYER1_ID")) else "",
            "player_in_id": str(int(ev["PLAYER2_ID"])) if pd.notna(ev.get("PLAYER2_ID")) else "",
        })
    return pd.DataFrame(rows, columns=cols)


@asset(
    partitions_def=season_partitions,
    group_name="nba_ontology",
    compute_kind="duckdb",
    deps=[raw_nba_pbp],
)
def nba_substitutions(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    from sportsml.sports.basketball.nba.ingestion import cache

    pbp = cache.load_cached("raw_nba_pbp", context.partition_key)
    if pbp is None or pbp.empty:
        import pandas as pd
        return Output(pd.DataFrame(), metadata={"rows": 0})
    df = extract_substitutions(pbp)
    return Output(df, metadata={"rows": len(df)})
