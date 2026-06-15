"""Synthetic-data test for the lineup_net_rating model."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
import numpy as np
import pandas as pd
import pytest
from sportsml.core.models.context import TenantContext
from sportsml.sports.basketball.nba.models.lineup_net_rating import (
    LineupNetRatingConfig,
    LineupNetRatingModel,
)


@contextmanager
def _ctx_with_stints(stints: pd.DataFrame):
    """Build a TenantContext pointing at a temp dir with on_off_stints seeded."""
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        feat = data_dir / "features" / "nba"
        feat.mkdir(parents=True)
        stints.to_parquet(feat / "on_off_stints.parquet", index=False)
        conn = duckdb.connect(":memory:")
        try:
            yield TenantContext(
                tenant_id="demo",
                sport_id="basketball.nba",
                duckdb_conn=conn,
                data_dir=data_dir,
            )
        finally:
            conn.close()


def _synthetic_stints(seed: int = 7) -> pd.DataFrame:
    """Three lineups, each playing many possessions; lineup A clearly best."""
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    # Three offensive 5-man groups for team T1; three opponents for T2.
    groups_off = [
        ["p1", "p2", "p3", "p4", "p5"],  # strong
        ["p6", "p7", "p8", "p9", "p10"],  # mid
        ["p11", "p12", "p13", "p14", "p15"],  # weak
    ]
    groups_def = [
        ["q1", "q2", "q3", "q4", "q5"],
        ["q6", "q7", "q8", "q9", "q10"],
        ["q11", "q12", "q13", "q14", "q15"],
    ]
    true_off = [+8.0, 0.0, -8.0]
    for off_idx, off_lu in enumerate(groups_off):
        for def_idx, def_lu in enumerate(groups_def):
            for k in range(50):  # 50 stints per pairing
                noise = rng.normal(0, 2.0)
                margin = true_off[off_idx] - true_off[def_idx] + noise
                rows.append(
                    {
                        "stint_id": f"s_{off_idx}_{def_idx}_{k}",
                        "game_id": f"g_{off_idx}_{def_idx}",
                        "off_team_id": "T1",
                        "def_team_id": "T2",
                        "off_player_ids": list(off_lu),
                        "def_player_ids": list(def_lu),
                        "possessions": 10,
                        "points_for": int(round(margin / 10.0) + 5),
                        "points_against": 5,
                        "point_margin_per_100": margin,
                    }
                )
    return pd.DataFrame(rows)


def test_model_returns_expected_shape_and_deterministic_top_lineup():
    stints = _synthetic_stints()
    model = LineupNetRatingModel()
    config = LineupNetRatingConfig(
        seasons=["2023-24"],
        min_possessions=50,
        rapm_lambda=10.0,
        prior_weight=0.5,
        three_point_emphasis=1.0,
    )
    with _ctx_with_stints(stints) as ctx:
        out = model.run(config, ctx)
    df = out.rows
    assert not df.empty, "Should return at least one scored lineup."
    expected_cols = {
        "lineup_id",
        "team_id",
        "player_ids",
        "projected_net",
        "ci_lo",
        "ci_hi",
        "sample_n",
    }
    assert expected_cols.issubset(df.columns)
    assert df.iloc[0]["projected_net"] > df.iloc[-1]["projected_net"]
    # The "strong" lineup is p1..p5.
    top_players = set(df.iloc[0]["player_ids"])
    assert top_players == {"p1", "p2", "p3", "p4", "p5"}


def test_min_possessions_filter_applied():
    stints = _synthetic_stints()
    model = LineupNetRatingModel()
    config = LineupNetRatingConfig(min_possessions=2000)  # Max allowed; nothing should pass.
    with _ctx_with_stints(stints) as ctx:
        out = model.run(config, ctx)
    assert out.rows.empty


def test_run_with_no_data_returns_empty_frame():
    model = LineupNetRatingModel()
    config = LineupNetRatingConfig()
    with TemporaryDirectory() as tmp:
        conn = duckdb.connect(":memory:")
        try:
            ctx = TenantContext(
                tenant_id="demo",
                sport_id="basketball.nba",
                duckdb_conn=conn,
                data_dir=Path(tmp),
            )
            out = model.run(config, ctx)
        finally:
            conn.close()
    assert out.rows.empty
    assert out.metadata.get("reason") == "no_data"


def test_invalid_config_type_raises():
    model = LineupNetRatingModel()
    with pytest.raises(TypeError):
        model.run({"min_possessions": 200}, None)  # type: ignore[arg-type]
