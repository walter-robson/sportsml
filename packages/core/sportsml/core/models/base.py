"""ModelTemplate ABC.

A ModelTemplate is a pure function ``(config, ctx) -> ModelRunOutput`` plus
declarative metadata (config_schema, output_schema, sport_id). The platform
auto-generates the slider UI from ``config_schema`` and persists output rows
under ``tenant_{id}.<model_name>`` in DuckDB.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sportsml.core.models.context import TenantContext
    from sportsml.core.models.runs import ModelRunOutput


class ModelTemplate(ABC):
    """Abstract base class for runnable model templates."""

    name: str
    version: str
    sport_id: str
    config_schema: type[BaseModel]
    output_schema: type[BaseModel]

    @abstractmethod
    def run(self, config: BaseModel, ctx: TenantContext) -> ModelRunOutput:
        """Execute the model. Pure: same (config, ctx data) ⇒ same output."""

    def describe(self) -> dict[str, object]:
        """Return a small JSON-friendly descriptor for ``GET /models``."""
        return {
            "id": self.name,
            "version": self.version,
            "sport_id": self.sport_id,
            "config_schema": self.config_schema.model_json_schema(),
            "output_schema": self.output_schema.model_json_schema(),
        }
