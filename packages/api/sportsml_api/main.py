"""FastAPI entrypoint.

Boots, mounts routers, and registers sport plugins by import. v0 wires only
``basketball.nba``; additional sports register by adding their plugin import
to ``_register_sport_plugins`` below.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sportsml_api.persistence import init_runs_db
from sportsml_api.routers import apps as apps_router
from sportsml_api.routers import datasets as datasets_router
from sportsml_api.routers import models as models_router
from sportsml_api.routers import ontology as ontology_router


def _register_sport_plugins() -> None:
    """Import sport plugin packages so their decorators register types + models."""
    import sportsml.sports.basketball.nba  # noqa: F401


def create_app() -> FastAPI:
    """App factory. Lets tests construct isolated instances."""
    _register_sport_plugins()
    init_runs_db()

    app = FastAPI(
        title="sportsml API",
        version="0.0.1",
        description="Foundry-style data platform for sports analytics.",
    )
    # Allow Workbench dev server on either 3000 (default) or 3001 (fallback when 3000 is in use).
    # Configurable via SPORTSML_CORS_ORIGINS (comma-separated) for non-default ports.
    import os
    cors_origins = os.environ.get(
        "SPORTSML_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001",
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(ontology_router.router, prefix="/ontology", tags=["ontology"])
    app.include_router(datasets_router.router, prefix="/datasets", tags=["datasets"])
    app.include_router(models_router.router, prefix="/models", tags=["models"])
    app.include_router(apps_router.router, prefix="/apps", tags=["apps"])
    return app


app = create_app()
