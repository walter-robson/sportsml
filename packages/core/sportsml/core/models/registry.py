"""Process-wide registry of ModelTemplate instances.

Sport plugins call ``register_model`` (typically via a decorator) at import
time. The FastAPI service imports the plugin to trigger registration, then
serves model metadata and runs via the registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sportsml.core.models.base import ModelTemplate


_REGISTRY: dict[str, ModelTemplate] = {}


def register_model(template: ModelTemplate) -> ModelTemplate:
    """Register a ModelTemplate instance.

    Usable as a decorator on a singleton instance, or called directly.
    Re-registering the same name overwrites — last writer wins, which makes
    hot-reload work cleanly in dev.
    """
    _REGISTRY[template.name] = template
    return template


def get_model(name: str) -> ModelTemplate:
    """Look up a registered ModelTemplate by name."""
    if name not in _REGISTRY:
        raise KeyError(f"No model registered under name {name!r}.")
    return _REGISTRY[name]


def list_models() -> list[ModelTemplate]:
    """Return all currently-registered templates."""
    return list(_REGISTRY.values())


def clear_registry() -> None:
    """Test helper. Not for production use."""
    _REGISTRY.clear()
