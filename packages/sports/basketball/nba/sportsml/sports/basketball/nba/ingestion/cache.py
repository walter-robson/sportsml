"""Local Parquet cache for nba_api responses.

The cache makes ingestion idempotent: a re-run of the same asset on the same
season returns the cached frame without hitting stats.nba.com again. The cache
key is the asset name plus stable identifiers (season, game_id, etc.).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def _cache_root() -> Path:
    return Path(os.environ.get("SPORTSML_DATA_DIR", "./data")).resolve() / "raw" / "nba"


def cache_path(asset: str, key: str) -> Path:
    """Stable filesystem path for an (asset, key) pair."""
    safe_key = key.replace("/", "_").replace(" ", "_")
    return _cache_root() / asset / f"{safe_key}.parquet"


def load_cached(asset: str, key: str) -> pd.DataFrame | None:
    import pandas as pd

    p = cache_path(asset, key)
    if not p.exists():
        return None
    return pd.read_parquet(p)


def save_cached(asset: str, key: str, df: pd.DataFrame) -> Path:
    p = cache_path(asset, key)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    return p
