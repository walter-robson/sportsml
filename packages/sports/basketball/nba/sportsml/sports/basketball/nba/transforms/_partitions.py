"""Shared partitions definition for NBA transform assets."""

from __future__ import annotations

from dagster import StaticPartitionsDefinition
from sportsml.sports.basketball.nba.ingestion.config import SEASON_V0

season_partitions = StaticPartitionsDefinition([SEASON_V0])
