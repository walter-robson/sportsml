"""Tenant context dependency.

v0: derives a single ``demo`` tenant from environment. When auth lands, this
dependency will inspect the JWT instead.
"""

from __future__ import annotations

from collections.abc import Iterator

from sportsml.core.models.context import TenantContext
from sportsml.core.tenancy.context import build_context


def get_tenant_context() -> Iterator[TenantContext]:
    """FastAPI dependency yielding a per-request TenantContext + DuckDB conn."""
    with build_context() as ctx:
        yield ctx
