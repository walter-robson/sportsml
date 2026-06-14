"""App framework: declarative layouts rendered by the Workbench."""

from __future__ import annotations

from sportsml.core.apps.base import App, AppLayout, AppPanel
from sportsml.core.apps.registry import get_app, list_apps, register_app

__all__ = [
    "App",
    "AppLayout",
    "AppPanel",
    "get_app",
    "list_apps",
    "register_app",
]
