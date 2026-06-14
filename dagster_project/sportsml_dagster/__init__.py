"""Dagster code location for sportsml.

v0 wires only the NBA sport plugin's assets. Additional sport plugins plug in
by appending their asset modules to ``SPORT_ASSET_MODULES`` below.
"""

from __future__ import annotations

import os
from pathlib import Path

from dagster import Definitions, load_assets_from_modules
from dagster_duckdb import DuckDBResource
from sportsml.sports.basketball.nba import ingestion as nba_ingestion
from sportsml.sports.basketball.nba import transforms as nba_transforms

SPORT_ASSET_MODULES = [nba_ingestion.assets, nba_transforms]


def _duckdb_path() -> str:
    data_dir = Path(os.environ.get("SPORTSML_DATA_DIR", "./data")).resolve()
    return os.environ.get("SPORTSML_DUCKDB_PATH", str(data_dir / "sportsml.duckdb"))


all_assets = []
for mod in SPORT_ASSET_MODULES:
    all_assets.extend(load_assets_from_modules([mod]))


defs = Definitions(
    assets=all_assets,
    resources={
        "duckdb": DuckDBResource(database=_duckdb_path()),
    },
)
