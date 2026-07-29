"""Version 1 API router."""

from fastapi import APIRouter

from musicbloom.api.schemas import HealthResponse, build_health_response

router = APIRouter(tags=["v1"])


@router.get("/health", response_model=HealthResponse)
def health_check_v1() -> HealthResponse:
    """Return versioned service health status."""
    return build_health_response()
