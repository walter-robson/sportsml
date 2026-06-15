"""RAPM design-matrix feature: one row per stint, +1/-1 per player on the floor.

For each stint we emit one row where:
- ``possessions`` = stint.possessions_played
- ``point_margin_per_100`` = (points_for - points_against) / poss * 100
- ``players_off`` = list of player_ids that were on offense
- ``players_def`` = list of player_ids that were on defense

The Ridge regression in the model layer turns these into sparse columns at
fit time. We don't materialize the wide matrix here — at ~30k players × 200k
stints that would balloon — we keep stints long and let scipy do the rest.
"""

import pandas as pd
from dagster import AssetExecutionContext, Output, asset
from sportsml.sports.basketball.nba.transforms._partitions import season_partitions
from sportsml.sports.basketball.nba.transforms.lineup_stints import nba_lineup_stints


def build_on_off_stints(stints: "pd.DataFrame") -> "pd.DataFrame":
    """Pair offense/defense stints from the same game for RAPM.

    Stints are emitted per-team; we self-join on game_id to attach each
    team's stint to its opponent's overlapping stint(s) and compute the
    relative point margin.

    For v0 simplicity we approximate "overlap" with a (game_id, possessions
    aligned by index) join: stints are already in possession-order within
    a game per team, and possession counts roughly match across teams.
    """
    import pandas as pd

    if stints is None or stints.empty:
        return pd.DataFrame(
            columns=[
                "stint_id",
                "game_id",
                "off_team_id",
                "def_team_id",
                "off_player_ids",
                "def_player_ids",
                "possessions",
                "points_for",
                "points_against",
                "point_margin_per_100",
            ]
        )

    rows: list[dict[str, object]] = []
    for game_id, g in stints.groupby("game_id"):
        teams = g["team_id"].unique().tolist()
        if len(teams) != 2:
            continue
        a, b = teams
        a_stints = g[g["team_id"] == a].reset_index(drop=True)
        b_stints = g[g["team_id"] == b].reset_index(drop=True)
        n = min(len(a_stints), len(b_stints))
        for i in range(n):
            off, deff = a_stints.iloc[i], b_stints.iloc[i]
            poss = int(off["possessions_played"])
            if poss <= 0:
                continue
            pf = int(off["points_for"])
            pa = int(off["points_against"])
            rows.append(
                {
                    "stint_id": f"{game_id}_{i}",
                    "game_id": game_id,
                    "off_team_id": off["team_id"],
                    "def_team_id": deff["team_id"],
                    "off_player_ids": list(off["player_ids"]),
                    "def_player_ids": list(deff["player_ids"]),
                    "possessions": poss,
                    "points_for": pf,
                    "points_against": pa,
                    "point_margin_per_100": (pf - pa) / poss * 100.0,
                }
            )
    return pd.DataFrame(rows)


@asset(
    partitions_def=season_partitions,
    group_name="nba_features",
    compute_kind="duckdb",
    deps=[nba_lineup_stints],
)
def nba_on_off_stints(
    context: AssetExecutionContext, nba_lineup_stints: "pd.DataFrame"
) -> Output[pd.DataFrame]:  # noqa: ARG001
    df = build_on_off_stints(nba_lineup_stints)
    return Output(df, metadata={"rows": len(df)})
