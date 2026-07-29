"""FastAPI application factory and route definitions."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from musicbloom import __version__

API_TITLE = "MusicBloom API"
SERVICE_NAME = "musicbloom-api"


class RootResponse(BaseModel):
    """Response model for the root endpoint."""

    name: str = Field(description="Application name")
    tagline: str = Field(description="Short project tagline")
    version: str = Field(description="API version")


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    status: str = Field(description="Service health status")
    service: str = Field(description="Service identifier")


app = FastAPI(
    title=API_TITLE,
    version=__version__,
    description=(
        "Backend API for MusicBloom — grow your music garden, one song at a time."
    ),
)


@app.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    """Return basic project metadata."""
    return RootResponse(
        name="MusicBloom",
        tagline="Grow your music garden, one song at a time.",
        version=__version__,
    )


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
    )
