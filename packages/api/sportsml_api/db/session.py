"""Session helpers — FastAPI dependency and stand-alone context manager."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from sportsml_api.db.engine import create_session_factory

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.orm import Session


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a Session that commits on clean exit, rolls back on exception."""
    factory = create_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency. ``Depends(get_session)`` yields a request-scoped Session."""
    factory = create_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
