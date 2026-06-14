"""NBA sport plugin: ontology + ingestion + transforms + models + apps.

Importing this package registers the ``lineup_net_rating`` ModelTemplate and
the ``lineup_analysis`` App into the core registries.
"""

from __future__ import annotations

# Side-effecting imports register the model and app on first import.
from sportsml.sports.basketball.nba.apps import lineup_analysis as _app  # noqa: F401
from sportsml.sports.basketball.nba.models import lineup_net_rating as _model  # noqa: F401

SPORT_ID = "basketball.nba"
