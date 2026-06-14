"""Dagster source assets that pull from ``nba_api``.

Two modes (env ``SPORTSML_INGEST_MODE``):
- "smoke" — only 50 games from January 2024 (default; fast for v0 demos).
- "full"  — all 1,230 regular-season games of 2023-24.

All endpoints rate-limit politely (``NBA_API_DELAY_S`` seconds between calls)
and retry transient failures with tenacity. Responses are cached to local
Parquet so re-runs are idempotent and free.
"""

from __future__ import annotations

from sportsml.sports.basketball.nba.ingestion.assets import nba_source_assets
from sportsml.sports.basketball.nba.ingestion.config import IngestionMode, ingestion_config

__all__ = ["IngestionMode", "ingestion_config", "nba_source_assets"]
