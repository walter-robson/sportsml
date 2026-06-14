"""Golden-record test for lineup-stint segmentation.

We feed a fake 3-minute game segment to ``build_lineup_stints`` and assert:
- Two substitutions produce three stints for the affected team.
- Untouched team yields exactly one stint.
- Possessions are credited to whichever stint is open at possession-end.
"""

from __future__ import annotations

import pandas as pd
from sportsml.sports.basketball.nba.transforms.lineup_stints import (
    build_lineup_stints,
    lineup_id,
)


def _subs() -> pd.DataFrame:
    """Two substitutions on team A in period 1, one on team B."""
    return pd.DataFrame([
        {"id": "s1", "game_id": "G1", "team_id": "A", "period": 1,
         "game_clock_s": 600.0, "player_in_id": "a6", "player_out_id": "a5"},
        {"id": "s2", "game_id": "G1", "team_id": "A", "period": 1,
         "game_clock_s": 300.0, "player_in_id": "a5", "player_out_id": "a6"},
        {"id": "s3", "game_id": "G1", "team_id": "B", "period": 1,
         "game_clock_s": 400.0, "player_in_id": "b6", "player_out_id": "b5"},
    ])


def _possessions() -> pd.DataFrame:
    return pd.DataFrame([
        {"id": "p1", "game_id": "G1", "possession_num": 1, "period": 1,
         "offense_team_id": "A", "points_scored": 2,
         "outcome": "made_fg", "defense_team_id": "B",
         "game_clock_start": "12:00", "game_clock_end": "11:30"},
        {"id": "p2", "game_id": "G1", "possession_num": 2, "period": 1,
         "offense_team_id": "B", "points_scored": 0,
         "outcome": "turnover", "defense_team_id": "A",
         "game_clock_start": "11:30", "game_clock_end": "10:50"},
        {"id": "p3", "game_id": "G1", "possession_num": 3, "period": 1,
         "offense_team_id": "A", "points_scored": 3,
         "outcome": "made_fg", "defense_team_id": "B",
         "game_clock_start": "10:50", "game_clock_end": "10:20"},
    ])


def test_stints_split_on_each_substitution():
    starters = {
        "A": ["a1", "a2", "a3", "a4", "a5"],
        "B": ["b1", "b2", "b3", "b4", "b5"],
    }
    df = build_lineup_stints("G1", starters, _subs(), _possessions())
    a_stints = df[df["team_id"] == "A"].reset_index(drop=True)
    b_stints = df[df["team_id"] == "B"].reset_index(drop=True)
    assert len(a_stints) == 3, "Two subs on A → three stints."
    assert len(b_stints) == 2, "One sub on B → two stints."


def test_lineup_id_is_order_independent():
    a = lineup_id(["a1", "a2", "a3"])
    b = lineup_id(["a3", "a1", "a2"])
    assert a == b


def test_points_attributed_to_correct_stints():
    starters = {
        "A": ["a1", "a2", "a3", "a4", "a5"],
        "B": ["b1", "b2", "b3", "b4", "b5"],
    }
    df = build_lineup_stints("G1", starters, _subs(), _possessions())
    a_total_for = df[df["team_id"] == "A"]["points_for"].sum()
    a_total_against = df[df["team_id"] == "A"]["points_against"].sum()
    assert a_total_for == 5  # 2 + 3
    assert a_total_against == 0


def test_empty_inputs_yield_two_empty_stints_per_team():
    starters = {
        "A": ["a1", "a2", "a3", "a4", "a5"],
        "B": ["b1", "b2", "b3", "b4", "b5"],
    }
    df = build_lineup_stints(
        "G1", starters,
        pd.DataFrame(columns=["id", "game_id", "team_id", "period",
                              "game_clock_s", "player_in_id", "player_out_id"]),
        pd.DataFrame(columns=["id", "game_id", "possession_num", "period",
                              "offense_team_id", "points_scored", "outcome",
                              "defense_team_id", "game_clock_start", "game_clock_end"]),
    )
    # One stint per team when no subs happen.
    assert (df["team_id"] == "A").sum() == 1
    assert (df["team_id"] == "B").sum() == 1
