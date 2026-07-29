"""Version 1 API router."""

from fastapi import APIRouter

from musicbloom.api.schemas import HealthResponse, build_health_response
from musicbloom.api.v1.routes.albums import router as albums_router
from musicbloom.api.v1.routes.artists import router as artists_router
from musicbloom.api.v1.routes.tracks import router as tracks_router

router = APIRouter(tags=["v1"])

router.include_router(tracks_router)
router.include_router(artists_router)
router.include_router(albums_router)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Return versioned service health status.",
)
def health_check_v1() -> HealthResponse:
    """Return versioned service health status."""
    return build_health_response()
