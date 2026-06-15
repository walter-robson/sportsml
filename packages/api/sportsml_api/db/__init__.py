"""Persistence layer: SQLAlchemy ORM models, engine, session.

Postgres is the production target (Supabase). The same models work against any
Postgres 14+, including a local docker-compose service.
"""

from sportsml_api.db.engine import (
    create_session_factory,
    dispose_engine,
    get_engine,
    init_engine,
)
from sportsml_api.db.models import Base, ModelRunRow, Tenant
from sportsml_api.db.session import get_session, session_scope

__all__ = [
    "Base",
    "ModelRunRow",
    "Tenant",
    "create_session_factory",
    "dispose_engine",
    "get_engine",
    "get_session",
    "init_engine",
    "session_scope",
]
