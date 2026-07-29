"""Azure DevOps Dev Garden routes."""

from fastapi import APIRouter

from musicbloom.api.v1.schemas.devops import DevOpsRunsResponse, DevOpsStatusResponse
from musicbloom.dependencies import DevOpsServiceDep

router = APIRouter(prefix="/devops", tags=["devops"])


@router.get(
    "/status",
    response_model=DevOpsStatusResponse,
    summary="Get Azure DevOps pipeline status",
    description=(
        "Return normalized pipeline health for the Dev Garden. "
        "Personal access tokens are never exposed to clients."
    ),
)
async def get_devops_status(
    devops_service: DevOpsServiceDep,
) -> DevOpsStatusResponse:
    """Return the latest Azure DevOps pipeline status."""
    return await devops_service.get_status()


@router.get(
    "/runs",
    response_model=DevOpsRunsResponse,
    summary="List recent Azure DevOps pipeline runs",
    description=(
        "Return recent normalized pipeline runs for the Dev Garden. "
        "Personal access tokens are never exposed to clients."
    ),
)
async def list_devops_runs(
    devops_service: DevOpsServiceDep,
) -> DevOpsRunsResponse:
    """Return recent Azure DevOps pipeline runs."""
    return await devops_service.list_runs()
