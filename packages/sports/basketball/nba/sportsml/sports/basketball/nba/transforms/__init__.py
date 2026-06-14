"""NBA transform assets: ontology layer + feature layer.

All assets are pure functions of upstream Parquet files. They're partitioned
by season (matching the source assets) and emit Parquet outputs the model
templates can read directly from DuckDB.
"""

from __future__ import annotations

from sportsml.sports.basketball.nba.transforms.lineup_stints import (
    build_lineup_stints,
    nba_lineup_stints,
)
from sportsml.sports.basketball.nba.transforms.lineups import nba_lineups
from sportsml.sports.basketball.nba.transforms.on_off_stints import (
    build_on_off_stints,
    nba_on_off_stints,
)
from sportsml.sports.basketball.nba.transforms.player_season_stats import (
    nba_player_season_stats,
)
from sportsml.sports.basketball.nba.transforms.possessions import (
    nba_possessions,
    segment_possessions,
)
from sportsml.sports.basketball.nba.transforms.shots import nba_shots
from sportsml.sports.basketball.nba.transforms.substitutions import (
    extract_substitutions,
    nba_substitutions,
)

nba_transform_assets = [
    nba_possessions,
    nba_shots,
    nba_substitutions,
    nba_lineup_stints,
    nba_lineups,
    nba_player_season_stats,
    nba_on_off_stints,
]

__all__ = [
    "build_lineup_stints",
    "build_on_off_stints",
    "extract_substitutions",
    "nba_lineup_stints",
    "nba_lineups",
    "nba_on_off_stints",
    "nba_player_season_stats",
    "nba_possessions",
    "nba_shots",
    "nba_substitutions",
    "nba_transform_assets",
    "segment_possessions",
]
