"""Lineup-stint segmentation: the most important NBA transform.

The pure function ``build_lineup_stints`` takes:
- starters_per_team: ``dict[team_id, list[player_id]]`` (initial 5 on-court each team)
- substitutions: DataFrame with cols ``(game_id, team_id, period, game_clock_s,
  player_in_id, player_out_id)``
- possessions: DataFrame with cols ``(game_id, possession_num, period,
  offense_team_id, points_scored, game_clock_start)``

and returns one row per continuous stint per team:

    (id, game_id, team_id, lineup_id, start_period, start_clock_s,
     end_period, end_clock_s, possessions_played, points_for, points_against)

``lineup_id`` is the canonical sha256 hash of the sorted player_ids tuple.

The state machine is deliberately simple: every sub event mutates the on-court
set for one team; we close the prior stint and open a new one. Possessions
that occur between two subs are attributed to whichever stint is open when
the possession ends. Period transitions reset clocks but keep the on-court
sets (Dagster pipeline can override starters per period if it has that data).
"""

import hashlib
from dataclasses import dataclass, field

import pandas as pd
from dagster import AssetExecutionContext, Output, asset
from sportsml.sports.basketball.nba.transforms._partitions import season_partitions
from sportsml.sports.basketball.nba.transforms.substitutions import nba_substitutions


def lineup_id(player_ids: list[str]) -> str:
    """Deterministic id for a 5-man lineup. Order-independent."""
    sorted_ids = sorted(str(p) for p in player_ids)
    h = hashlib.sha256(("|".join(sorted_ids)).encode("utf-8")).hexdigest()
    return f"L_{h[:16]}"


@dataclass(slots=True)
class _OpenStint:
    team_id: str
    lineup_id: str
    player_ids: tuple[str, ...]
    start_period: int
    start_clock_s: float
    possessions: int = 0
    points_for: int = 0
    points_against: int = 0


@dataclass(slots=True)
class _GameState:
    """Mutable per-team on-court set tracker for one game."""

    on_court: dict[str, set[str]] = field(default_factory=dict)
    open_stints: dict[str, _OpenStint] = field(default_factory=dict)
    closed_stints: list[dict[str, object]] = field(default_factory=list)


def _open_stint(state: _GameState, team_id: str, period: int, clock_s: float) -> None:
    players = sorted(state.on_court.get(team_id, set()))
    lid = lineup_id(players)
    state.open_stints[team_id] = _OpenStint(
        team_id=team_id,
        lineup_id=lid,
        player_ids=tuple(players),
        start_period=period,
        start_clock_s=clock_s,
    )


def _close_stint(
    state: _GameState,
    team_id: str,
    period: int,
    clock_s: float,
    game_id: str,
) -> None:
    if team_id not in state.open_stints:
        return
    s = state.open_stints.pop(team_id)
    state.closed_stints.append({
        "id": f"{game_id}_{team_id}_{len(state.closed_stints)}",
        "game_id": game_id,
        "team_id": s.team_id,
        "lineup_id": s.lineup_id,
        "player_ids": list(s.player_ids),
        "start_period": s.start_period,
        "start_clock_s": s.start_clock_s,
        "end_period": period,
        "end_clock_s": clock_s,
        "possessions_played": s.possessions,
        "points_for": s.points_for,
        "points_against": s.points_against,
    })


def build_lineup_stints(
    game_id: str,
    starters_per_team: dict[str, list[str]],
    substitutions: "pd.DataFrame",
    possessions: "pd.DataFrame",
) -> "pd.DataFrame":
    """Pure segmentation: starters + subs + possessions → stints."""
    import pandas as pd

    state = _GameState()
    teams = list(starters_per_team.keys())
    if len(teams) != 2:
        raise ValueError(f"Expected exactly 2 teams, got {len(teams)} for {game_id!r}.")

    for tid, players in starters_per_team.items():
        state.on_court[tid] = {str(p) for p in players}
        _open_stint(state, tid, period=1, clock_s=12 * 60.0)

    sub_rows = (
        substitutions[substitutions["game_id"] == game_id]
        .sort_values(["period", "game_clock_s"], ascending=[True, False])
        .to_dict("records")
    ) if not substitutions.empty else []

    poss_rows = (
        possessions[possessions["game_id"] == game_id]
        .sort_values(["possession_num"])
        .to_dict("records")
    ) if not possessions.empty else []

    # Interleave possession crediting and sub events by (period, -clock_s) order.
    # Possessions are credited to the stint open at the moment the possession ends.
    events: list[tuple[tuple[int, float], str, dict]] = []
    for sub in sub_rows:
        events.append(((int(sub["period"]), -float(sub["game_clock_s"])), "sub", sub))
    for p in poss_rows:
        # Use period and end clock; v0 doesn't track end-clock-s precisely, so we
        # synthesize a stable monotone key from period + possession_num.
        events.append((
            (int(p["period"]), float(p["possession_num"])), "poss", p,
        ))
    events.sort(key=lambda e: e[0])

    for (period, _), kind, ev in events:
        if kind == "poss":
            off = str(ev["offense_team_id"])
            pts = int(ev["points_scored"])
            defense = next((t for t in teams if t != off), None)
            if off in state.open_stints:
                state.open_stints[off].possessions += 1
                state.open_stints[off].points_for += pts
            if defense and defense in state.open_stints:
                state.open_stints[defense].possessions += 1
                state.open_stints[defense].points_against += pts
        elif kind == "sub":
            tid = str(ev["team_id"])
            clock_s = float(ev["game_clock_s"])
            pin = str(ev["player_in_id"])
            pout = str(ev["player_out_id"])
            _close_stint(state, tid, period, clock_s, game_id)
            on = state.on_court.setdefault(tid, set())
            on.discard(pout)
            on.add(pin)
            _open_stint(state, tid, period, clock_s)

    for tid in teams:
        _close_stint(state, tid, period=4, clock_s=0.0, game_id=game_id)

    cols = [
        "id", "game_id", "team_id", "lineup_id", "player_ids",
        "start_period", "start_clock_s", "end_period", "end_clock_s",
        "possessions_played", "points_for", "points_against",
    ]
    return pd.DataFrame(state.closed_stints, columns=cols)


@asset(
    partitions_def=season_partitions,
    group_name="nba_ontology",
    compute_kind="duckdb",
    deps=[nba_substitutions],
)
def nba_lineup_stints(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """Stints across all ingested games for the partition season.

    Starters are derived from each game's box score (rows where MIN > 0 and
    START_POSITION is set). If a game's starters can't be resolved we skip it.
    """
    import pandas as pd
    from sportsml.sports.basketball.nba.ingestion import cache

    subs = cache.load_cached("raw_nba_pbp", context.partition_key)
    box = cache.load_cached("raw_nba_box_scores", context.partition_key)
    if subs is None or box is None or box.empty:
        return Output(pd.DataFrame(), metadata={"rows": 0, "games": 0})

    # We need the materialized substitutions + possessions assets here, but
    # to keep things v0-simple we recompute them inline from the cached PBP.
    from sportsml.sports.basketball.nba.transforms.possessions import segment_possessions
    from sportsml.sports.basketball.nba.transforms.substitutions import extract_substitutions

    subs_df = extract_substitutions(subs)
    poss_df = segment_possessions(subs)

    all_stints: list[pd.DataFrame] = []
    starters_col = "START_POSITION"
    for game_id, gbx in box.groupby("GAME_ID", sort=False):
        gbx_starters = gbx[gbx[starters_col].fillna("").str.strip() != ""]
        teams = gbx_starters["TEAM_ID"].astype(str).unique().tolist()
        if len(teams) != 2:
            continue
        starters = {
            str(t): gbx_starters[gbx_starters["TEAM_ID"].astype(str) == str(t)]
                .head(5)["PLAYER_ID"].astype(str).tolist()
            for t in teams
        }
        if any(len(v) != 5 for v in starters.values()):
            continue
        all_stints.append(build_lineup_stints(str(game_id), starters, subs_df, poss_df))

    df = pd.concat(all_stints, ignore_index=True) if all_stints else pd.DataFrame()
    return Output(df, metadata={"rows": len(df), "games": len(all_stints)})
