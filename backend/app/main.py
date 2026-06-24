###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import alarms, config, exports, imports, tags
from app.config import Settings
from app.services.session import SessionState


@asynccontextmanager
async def _lifespan(app: FastAPI):
    app.state.session = SessionState()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    FastAPI application factory.
    Pass a custom Settings instance to override env-based config (useful in tests).
    """
    from app.config import get_settings

    application = FastAPI(
        title="IOManager",
        description="ETL pipeline for Twinsoft PLC tag and alarm import generation",
        version="1.0.0",
        lifespan=_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings is not None:
        application.dependency_overrides[get_settings] = lambda: settings

    application.include_router(imports.router, prefix="/api/imports")
    application.include_router(exports.router, prefix="/api/exports")
    application.include_router(tags.router, prefix="/api")
    application.include_router(alarms.router, prefix="/api")
    application.include_router(config.router, prefix="/api")

    return application


# Module-level instance for uvicorn / docker compose
app = create_app()
