"""FastAPI dependency injection helpers."""

from __future__ import annotations

from sportsml_api.deps.context import get_tenant_context

__all__ = ["get_tenant_context"]
