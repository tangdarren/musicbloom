"""FastAPI application factory and route definitions."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import Engine

from musicbloom.api.schemas import (
    HealthResponse,
    RootResponse,
    build_health_response,
    build_root_response,
)
from musicbloom.api.v1.player_handlers import register_player_exception_handlers
from musicbloom.api.v1.progression_handlers import (
    register_progression_exception_handlers,
)
from musicbloom.api.v1.quest_handlers import register_quest_exception_handlers
from musicbloom.api.v1.router import router as v1_router
from musicbloom.config import Settings
from musicbloom.constants import API_DESCRIPTION, API_TITLE, __version__
from musicbloom.db.init import initialize_database
from musicbloom.db.session import create_database_engine
from musicbloom.dependencies import get_settings


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        db_engine = engine or create_database_engine(app_settings.resolved_database_url)
        initialize_database(db_engine, app_settings)
        yield

    application = FastAPI(
        title=API_TITLE,
        version=__version__,
        description=API_DESCRIPTION,
        debug=app_settings.debug,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(v1_router, prefix="/api/v1")
    register_player_exception_handlers(application)
    register_progression_exception_handlers(application)
    register_quest_exception_handlers(application)

    static_dir = Path(__file__).resolve().parents[3] / "static"
    if static_dir.is_dir():
        application.mount("/static", StaticFiles(directory=static_dir), name="static")

    @application.get("/", response_model=RootResponse)
    def read_root() -> RootResponse:
        """Return basic project metadata."""
        return build_root_response()

    @application.get("/api/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """Return service health status."""
        return build_health_response()

    return application


app = create_app()
