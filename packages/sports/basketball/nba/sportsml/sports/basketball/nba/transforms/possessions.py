"""Derive Possessions from raw PBP.

v0 segmentation is intentionally minimal: a possession ends on a made FG,
defensive rebound, turnover, foul drawing FTs, or end-of-period. We do not
attempt to use ``pbpstats`` in v0 — it adds a heavy dependency and our smoke
data is small enough that a DuckDB SQL pass is fine.

Known limitations (acceptable for v0):
- Technical FTs are treated as their own possession boundary.
- Jump-ball edge cases inside a period are not resolved.
- And-1 sequences may be split into two possessions.
"""

import pandas as pd
from dagster import AssetExecutionContext, Output, asset
from sportsml.sports.basketball.nba.ingestion.assets import raw_nba_pbp
from sportsml.sports.basketball.nba.transforms._partitions import season_partitions

# Event-type constants from nba_api PBP feed.
EVENT_MADE_SHOT = 1
EVENT_MISSED_SHOT = 2
EVENT_FREE_THROW = 3
EVENT_REBOUND = 4
EVENT_TURNOVER = 5
EVENT_FOUL = 6
EVENT_SUBSTITUTION = 8
EVENT_PERIOD_END = 13


def segment_possessions(pbp: "pd.DataFrame") -> "pd.DataFrame":
    """Pure function: PBP events → one row per possession.

    Pulled out of the Dagster asset so it's directly testable with synthetic
    PBP. Returns ``(game_id, possession_num, period, outcome, points_scored,
    offense_team_id, defense_team_id, possession_seconds)``.
    """
    import pandas as pd

    if pbp.empty:
        return pd.DataFrame(
            columns=[
                "id", "game_id", "possession_num", "period", "outcome",
                "points_scored", "offense_team_id", "defense_team_id",
                "game_clock_start", "game_clock_end",
            ]
        )

    out_rows: list[dict[str, object]] = []
    for game_id, game_pbp in pbp.groupby("GAME_ID", sort=False):
        game_pbp = game_pbp.sort_values(["PERIOD", "EVENTNUM"]).reset_index(drop=True)
        offense_team: int | None = None
        clock_start: str | None = None
        points: int = 0
        possession_num = 0
        period_now = int(game_pbp.iloc[0]["PERIOD"])

        # ``flush`` is invoked synchronously inside the loop; the period and
        # game_id are passed explicitly to avoid the late-binding hazard
        # (ruff's B023).
        def flush(
            end_clock: str,
            outcome: str,
            current_game: str,
            current_period: int,
        ) -> None:
            nonlocal possession_num, points, clock_start, offense_team
            if offense_team is None:
                return
            possession_num += 1
            out_rows.append({
                "id": f"{current_game}_{possession_num}",
                "game_id": str(current_game),
                "possession_num": possession_num,
                "period": current_period,
                "outcome": outcome,
                "points_scored": points,
                "offense_team_id": str(offense_team),
                "defense_team_id": "",
                "game_clock_start": clock_start or "",
                "game_clock_end": end_clock,
            })
            offense_team = None
            clock_start = None
            points = 0

        for _, ev in game_pbp.iterrows():
            ev_type = int(ev.get("EVENTMSGTYPE", 0))
            period = int(ev.get("PERIOD", 0))
            clock = str(ev.get("PCTIMESTRING", ""))
            team = ev.get("PLAYER1_TEAM_ID")

            if period != period_now and offense_team is not None:
                flush(clock, "end_period", str(game_id), period_now)
                period_now = period

            if ev_type == EVENT_MADE_SHOT:
                if offense_team is None:
                    offense_team = int(team) if pd.notna(team) else None
                    clock_start = clock
                desc = str(ev.get("HOMEDESCRIPTION") or ev.get("VISITORDESCRIPTION") or "")
                points = 3 if "3PT" in desc.upper() else 2
                flush(clock, "made_fg", str(game_id), period_now)
            elif ev_type == EVENT_MISSED_SHOT:
                if offense_team is None and pd.notna(team):
                    offense_team = int(team)
                    clock_start = clock
            elif ev_type == EVENT_TURNOVER:
                if offense_team is None and pd.notna(team):
                    offense_team = int(team)
                    clock_start = clock
                flush(clock, "turnover", str(game_id), period_now)
            elif ev_type == EVENT_REBOUND:
                # Defensive rebound flips possession; offensive rebound continues it.
                if offense_team is not None and pd.notna(team) and int(team) != offense_team:
                    flush(clock, "missed_fg", str(game_id), period_now)
            elif ev_type == EVENT_PERIOD_END:
                flush(clock, "end_period", str(game_id), period_now)

        if offense_team is not None:
            flush("00:00", "end_period", str(game_id), period_now)

    cols = [
        "id", "game_id", "possession_num", "period", "outcome",
        "points_scored", "offense_team_id", "defense_team_id",
        "game_clock_start", "game_clock_end",
    ]
    return pd.DataFrame(out_rows, columns=cols)


@asset(
    partitions_def=season_partitions,
    group_name="nba_ontology",
    compute_kind="duckdb",
    deps=[raw_nba_pbp],
)
def nba_possessions(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Materialize segmented possessions for one season partition."""
    from sportsml.sports.basketball.nba.ingestion import cache

    # raw_nba_pbp asset caches its DataFrame under the same key.
    pbp = cache.load_cached("raw_nba_pbp", context.partition_key)
    if pbp is None or pbp.empty:
        import pandas as pd
        df = pd.DataFrame()
    else:
        df = segment_possessions(pbp)
    context.log.info(f"Built {len(df)} possessions.")
    return Output(df, metadata={"rows": len(df)})
