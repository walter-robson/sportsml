"""SQLAlchemy engine + session factory wired through env vars.

The engine is module-global so all callers share a connection pool. Tests reset
it via :func:`init_engine` and :func:`dispose_engine`.
"""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10


def database_url() -> str:
    """Return the configured DATABASE_URL.

    Falls back to a local docker-compose Postgres for dev convenience. CI and
    prod must set ``SPORTSML_DATABASE_URL`` explicitly.
    """
    return os.environ.get(
        "SPORTSML_DATABASE_URL",
        "postgresql+psycopg://sportsml:sportsml@localhost:5432/sportsml",
    )


def init_engine(url: str | None = None) -> Engine:
    """Create (or replace) the global engine + session factory.

    Safe to call multiple times; previous engine is disposed first. SQLite
    URLs get a single-connection StaticPool (used by the test suite).
    """
    global _engine, _session_factory
    dispose_engine()
    resolved = url or database_url()
    if resolved.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool

        _engine = create_engine(
            resolved,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    else:
        _engine = create_engine(
            resolved,
            pool_size=DEFAULT_POOL_SIZE,
            max_overflow=DEFAULT_MAX_OVERFLOW,
            pool_pre_ping=True,
            future=True,
        )
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        return init_engine()
    return _engine


def create_session_factory() -> sessionmaker[Session]:
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    return _session_factory


def dispose_engine() -> None:
    """Tear down the global engine. Safe to call when nothing is initialized."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
