"""Pydantic response models for HTTP endpoints."""

from pydantic import BaseModel, Field

from musicbloom.constants import APP_NAME, APP_TAGLINE, SERVICE_NAME, __version__


class RootResponse(BaseModel):
    """Response model for the root endpoint."""

    name: str = Field(description="Application name")
    tagline: str = Field(description="Short project tagline")
    version: str = Field(description="API version")


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    status: str = Field(description="Service health status")
    service: str = Field(description="Service identifier")


def build_root_response() -> RootResponse:
    """Build the standard root metadata response."""
    return RootResponse(
        name=APP_NAME,
        tagline=APP_TAGLINE,
        version=__version__,
    )


def build_health_response() -> HealthResponse:
    """Build the standard health check response."""
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
    )
