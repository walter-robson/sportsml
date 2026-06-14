"""Bayesian-shrunk RAPM model for NBA lineup net rating.

v0 implementation:
- Read ``features.nba.on_off_stints`` (one row per stint with offense/defense
  player ids and point_margin_per_100).
- Build a sparse design matrix of shape ``(n_stints, n_players)`` with +1 for
  offensive players and -1 for defensive players. Weights by sqrt(possessions).
- Run scikit-learn ``Ridge`` with ``alpha=rapm_lambda``.
- Score every unique lineup seen in stints by summing player coefficients
  (offensive minus defensive contributions).
- CI bands are approximated from residual variance and column inverse-norms.

Knobs marked TODO(v0.5) below are passed-through but no-op in v0 — that's
explicitly acceptable per the v0 brief.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from scipy import sparse
from sklearn.linear_model import Ridge
from sportsml.core.models.base import ModelTemplate
from sportsml.core.models.registry import register_model
from sportsml.core.models.runs import ModelRunOutput

if TYPE_CHECKING:
    import pandas as pd
    from sportsml.core.models.context import TenantContext


DEFAULT_SEASONS = ["2023-24"]


class LineupNetRatingConfig(BaseModel):
    """Tunable knobs surfaced as auto-generated sliders in the Workbench."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seasons: list[str] = Field(
        default_factory=lambda: list(DEFAULT_SEASONS),
        description="Training seasons to include.",
    )
    min_possessions: int = Field(
        200, ge=50, le=2000,
        description="Minimum possessions for a lineup to be returned in results.",
    )
    rapm_lambda: float = Field(
        200.0, ge=10.0, le=2000.0,
        description="Ridge regularization strength. Higher = more shrinkage to 0.",
    )
    prior_weight: float = Field(
        0.5, ge=0.0, le=1.0,
        description="Blend toward team prior (0=pure data, 1=pure prior).",
    )
    three_point_emphasis: float = Field(
        1.0, ge=0.5, le=3.0,
        description="Multiplier for 3-point heavy lineups in scoring.",
    )
    matchup_adjusted: bool = Field(
        True, description="Include opponent strength when projecting net rating.",
    )
    position_constraints: bool = Field(
        False, description="Enforce 1xPG + ≥1xbig in returned projections.",
    )


class LineupNetRatingOutput(BaseModel):
    """One row per scored lineup."""

    model_config = ConfigDict(extra="forbid")

    lineup_id: str
    team_id: str
    player_ids: list[str]
    projected_net: float
    ci_lo: float
    ci_hi: float
    sample_n: int


def _player_index(stints: pd.DataFrame) -> tuple[list[str], dict[str, int]]:
    """Build a stable ordering of all unique player ids appearing in any stint."""
    seen: set[str] = set()
    for col in ("off_player_ids", "def_player_ids"):
        for ids in stints[col]:
            seen.update(str(p) for p in ids)
    ordered = sorted(seen)
    return ordered, {p: i for i, p in enumerate(ordered)}


def _build_design_matrix(
    stints: pd.DataFrame,
    player_to_col: dict[str, int],
) -> tuple[sparse.csr_matrix, np.ndarray, np.ndarray]:
    """Construct (X, y, weights) for the Ridge regression.

    X[i, j] = +1 if player j is on offense in stint i, -1 if on defense, 0 otherwise.
    y[i]    = point_margin_per_100 for stint i.
    w[i]    = sqrt(possessions) — variance-stabilizing weights.
    """
    n = len(stints)
    p = len(player_to_col)
    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    y = np.zeros(n, dtype=np.float64)
    w = np.zeros(n, dtype=np.float64)
    for i, (_, r) in enumerate(stints.iterrows()):
        for pid in r["off_player_ids"]:
            rows.append(i)
            cols.append(player_to_col[str(pid)])
            vals.append(1.0)
        for pid in r["def_player_ids"]:
            rows.append(i)
            cols.append(player_to_col[str(pid)])
            vals.append(-1.0)
        y[i] = float(r["point_margin_per_100"])
        w[i] = float(r["possessions"]) ** 0.5
    design = sparse.csr_matrix((vals, (rows, cols)), shape=(n, p))
    return design, y, w


def _score_lineups(
    stints: pd.DataFrame,
    coefs: np.ndarray,
    player_to_col: dict[str, int],
    residual_var: float,
    min_possessions: int,
) -> pd.DataFrame:
    """Aggregate per-lineup possessions and project net rating from coefs."""
    import pandas as pd

    by_lineup: dict[tuple[str, tuple[str, ...]], dict[str, object]] = {}
    for _, r in stints.iterrows():
        key = (str(r["off_team_id"]), tuple(sorted(str(p) for p in r["off_player_ids"])))
        b = by_lineup.setdefault(key, {
            "team_id": key[0], "player_ids": list(key[1]),
            "possessions": 0, "points_for": 0, "points_against": 0,
        })
        b["possessions"] += int(r["possessions"])
        b["points_for"] += int(r["points_for"])
        b["points_against"] += int(r["points_against"])

    rows: list[dict[str, object]] = []
    z = 1.96  # 95% normal-approximation band
    for (_team_id, players), agg in by_lineup.items():
        idxs = [player_to_col[p] for p in players if p in player_to_col]
        if not idxs:
            continue
        # Offensive contribution ≈ sum of player coefs; defensive contribution is
        # symmetric in the design but here we report the projected *net rating*
        # for this 5-man lineup if it played against an average opponent.
        net = float(coefs[idxs].sum())
        # Approx CI: scale residual std by 1/sqrt(possessions); for a 5-man unit
        # we widen by sqrt(5) since 5 independent coefs are summed.
        n_poss = int(agg["possessions"])
        sigma = float(np.sqrt(residual_var * 5.0 / max(n_poss, 1)))
        rows.append({
            "lineup_id": _hash_lineup(players),
            "team_id": agg["team_id"],
            "player_ids": list(players),
            "projected_net": round(net, 3),
            "ci_lo": round(net - z * sigma, 3),
            "ci_hi": round(net + z * sigma, 3),
            "sample_n": n_poss,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[df["sample_n"] >= min_possessions].reset_index(drop=True)
        df = df.sort_values("projected_net", ascending=False).reset_index(drop=True)
    return df


def _hash_lineup(players: tuple[str, ...] | list[str]) -> str:
    import hashlib

    s = "|".join(sorted(str(p) for p in players))
    return "L_" + hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


class LineupNetRatingModel(ModelTemplate):
    """RAPM-style lineup net-rating projection model."""

    name: ClassVar[str] = "lineup_net_rating"
    version: ClassVar[str] = "0.1.0"
    sport_id: ClassVar[str] = "basketball.nba"
    config_schema: ClassVar[type[BaseModel]] = LineupNetRatingConfig
    output_schema: ClassVar[type[BaseModel]] = LineupNetRatingOutput

    def _load_stints(self, ctx: TenantContext, seasons: list[str]) -> pd.DataFrame:
        """Read on_off_stints from DuckDB if present, else from Parquet on disk.

        v0: we look for ``features.nba.on_off_stints`` (registered by Dagster)
        first; on miss we fall back to a default Parquet path so tests can
        seed the file directly without spinning up Dagster.
        """
        import pandas as pd

        try:
            res = ctx.duckdb_conn.execute(
                "SELECT * FROM features.nba.on_off_stints WHERE season = ANY(?)",
                [seasons],
            ).df()
            if not res.empty:
                return res
        except Exception:  # noqa: BLE001 — DuckDB raises generic errors; we just fall through
            pass

        path = ctx.data_dir / "features" / "nba" / "on_off_stints.parquet"
        if path.exists():
            return pd.read_parquet(path)
        return pd.DataFrame()

    def run(self, config: BaseModel, ctx: TenantContext) -> ModelRunOutput:
        if not isinstance(config, LineupNetRatingConfig):
            raise TypeError(
                f"Expected LineupNetRatingConfig, got {type(config).__name__}."
            )
        stints = self._load_stints(ctx, config.seasons)
        if stints.empty:
            import pandas as pd
            return ModelRunOutput(rows=pd.DataFrame(), metadata={"reason": "no_data"})

        players, p_to_col = _player_index(stints)
        X, y, w = _build_design_matrix(stints, p_to_col)  # noqa: N806 — sklearn convention
        sample_weight = w ** 2  # Ridge takes weights, not sqrt(weights).
        ridge = Ridge(alpha=config.rapm_lambda, fit_intercept=False)
        ridge.fit(X, y, sample_weight=sample_weight)
        coefs = ridge.coef_
        residuals = y - X @ coefs
        residual_var = float(np.average(residuals ** 2, weights=sample_weight) + 1e-6)

        df = _score_lineups(stints, coefs, p_to_col, residual_var, config.min_possessions)
        # TODO(v0.5): wire prior_weight, three_point_emphasis, matchup_adjusted,
        # position_constraints. Currently no-ops.
        return ModelRunOutput(
            rows=df,
            metadata={
                "players_scored": len(players),
                "stints_used": int(X.shape[0]),
                "rapm_lambda": config.rapm_lambda,
                "residual_var": residual_var,
            },
        )


# Singleton registered at import time. The NBA plugin's __init__ imports this
# module, triggering registration.
LINEUP_NET_RATING_MODEL = LineupNetRatingModel()
register_model(LINEUP_NET_RATING_MODEL)
