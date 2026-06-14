"""Process-wide App registry, parallel to the model registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sportsml.core.apps.base import App


_REGISTRY: dict[str, App] = {}


def register_app(app: App) -> App:
    _REGISTRY[app.id] = app
    return app


def get_app(app_id: str) -> App:
    if app_id not in _REGISTRY:
        raise KeyError(f"No app registered under id {app_id!r}.")
    return _REGISTRY[app_id]


def list_apps() -> list[App]:
    return list(_REGISTRY.values())


def clear_registry() -> None:
    _REGISTRY.clear()
