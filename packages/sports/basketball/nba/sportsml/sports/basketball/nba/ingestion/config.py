"""Ingestion configuration driven by environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum

SEASON_V0 = "2023-24"
SMOKE_GAME_LIMIT = 50
SMOKE_DATE_FROM = "01/01/2024"
SMOKE_DATE_TO = "01/31/2024"


class IngestionMode(StrEnum):
    SMOKE = "smoke"
    FULL = "full"


@dataclass(frozen=True, slots=True)
class IngestionConfig:
    """Environment-resolved ingestion settings."""

    mode: IngestionMode
    season: str
    api_delay_s: float
    api_retries: int
    api_timeout: int


def ingestion_config() -> IngestionConfig:
    mode_raw = os.environ.get("SPORTSML_INGEST_MODE", "smoke").lower()
    try:
        mode = IngestionMode(mode_raw)
    except ValueError:
        mode = IngestionMode.SMOKE
    return IngestionConfig(
        mode=mode,
        season=os.environ.get("SPORTSML_NBA_SEASON", SEASON_V0),
        api_delay_s=float(os.environ.get("NBA_API_DELAY_S", "0.6")),
        api_retries=int(os.environ.get("NBA_API_RETRIES", "3")),
        api_timeout=int(os.environ.get("NBA_API_TIMEOUT", "30")),
    )
