"""Base classes for the typed Ontology layer.

An ``ObjectType`` is a Pydantic v2 model representing a row in a typed dataset.
Sport plugins subclass ``ObjectType`` (transitively, through core types) to
declare sport-specific entities like ``Possession`` or ``Shot``.

``Property`` and ``Link`` are declarative metadata containers describing the
schema of an ObjectType in a sport-agnostic way; they're used by the Workbench
to render Ontology browsers without leaking sport-specific code into core.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True, slots=True)
class Property:
    """Declarative description of a field on an ObjectType.

    Mirrors the underlying Pydantic field but is sport-agnostic and serializable
    so the Workbench can render schemas without importing model classes.
    """

    name: str
    type: str
    nullable: bool = False
    description: str | None = None


@dataclass(frozen=True, slots=True)
class Link:
    """Declarative relationship between ObjectTypes.

    Cardinalities:
    - "one"  — exactly one related instance
    - "many" — zero or more related instances
    - "five" — basketball-specific lineup link; sport plugins may add more.
    """

    name: str
    target: str
    cardinality: str
    description: str | None = None


class ObjectType(BaseModel):
    """Base for every typed row across the platform.

    Subclasses declare:
    - ``__type_name__`` — public registry key (e.g. ``"core.player"``)
    - ``__properties__`` — list[Property]
    - ``__links__`` — list[Link]

    These metadata attributes are consumed by the Workbench Ontology browser.
    """

    model_config = ConfigDict(extra="forbid", frozen=False, populate_by_name=True)

    __type_name__: ClassVar[str] = "core.object"
    __properties__: ClassVar[list[Property]] = []
    __links__: ClassVar[list[Link]] = []

    @classmethod
    def type_name(cls) -> str:
        return cls.__type_name__

    @classmethod
    def schema_dict(cls) -> dict[str, object]:
        """Return a sport-agnostic schema description for the Workbench."""
        from dataclasses import asdict

        return {
            "type_name": cls.__type_name__,
            "properties": [asdict(p) for p in cls.__properties__],
            "links": [asdict(link) for link in cls.__links__],
            "pydantic_schema": cls.model_json_schema(),
        }
