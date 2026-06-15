"""Lineup Analysis app: the v0 hero.

Declares its layout in pure Python; the Workbench renders generic panels
without sport-aware code.
"""

from __future__ import annotations

from typing import ClassVar

from sportsml.core.apps.base import App, AppLayout, AppPanel
from sportsml.core.apps.registry import register_app


class LineupAnalysisApp(App):
    """NBA lineup analysis hero app."""

    id: ClassVar[str] = "lineup_analysis"
    sport_id: ClassVar[str] = "basketball.nba"
    name: ClassVar[str] = "Lineup Analysis"
    description: ClassVar[str] = (
        "Score every observed 5-man lineup with Bayesian-shrunk RAPM. "
        "Drag sliders to retune, click Run, watch the table re-sort."
    )
    models_used: ClassVar[list[str]] = ["lineup_net_rating"]
    layout: ClassVar[AppLayout] = AppLayout(
        left=[
            AppPanel(
                id="config",
                kind="config",
                title="Configuration",
                options={"model_id": "lineup_net_rating"},
            ),
        ],
        main=[
            AppPanel(
                id="top_lineups",
                kind="table",
                title="Top Lineups",
                options={
                    "model_id": "lineup_net_rating",
                    "sort": "-projected_net",
                    "columns": [
                        "lineup_id",
                        "team_id",
                        "player_ids",
                        "projected_net",
                        "ci_lo",
                        "ci_hi",
                        "sample_n",
                    ],
                },
            ),
            AppPanel(
                id="projection_vs_observed",
                kind="chart",
                title="Projection vs Observed",
                options={"x": "raw_net", "y": "projected_net"},
            ),
            AppPanel(
                id="two_man_synergy",
                kind="heatmap",
                title="2-Man Synergy",
                options={"axis_players": "team_top_10"},
            ),
        ],
    )


LINEUP_ANALYSIS_APP = LineupAnalysisApp()
register_app(LINEUP_ANALYSIS_APP)
