"""FastAPI application factory and route definitions."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from musicbloom.api.schemas import (
    HealthResponse,
    RootResponse,
    build_health_response,
    build_root_response,
)
from musicbloom.api.v1.router import router as v1_router
from musicbloom.config import Settings
from musicbloom.constants import API_DESCRIPTION, API_TITLE, __version__
from musicbloom.dependencies import get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app_settings = settings or get_settings()

    application = FastAPI(
        title=API_TITLE,
        version=__version__,
        description=API_DESCRIPTION,
        debug=app_settings.debug,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(v1_router, prefix="/api/v1")

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
