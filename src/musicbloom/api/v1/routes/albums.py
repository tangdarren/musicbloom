"""Demo catalog album routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from musicbloom.api.v1.schemas.catalog import Album
from musicbloom.dependencies import get_catalog_service
from musicbloom.services.catalog import CatalogService

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get(
    "",
    response_model=list[Album],
    summary="List demo albums",
    description="Return all fictional albums included in the demo catalog.",
)
def list_albums(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> list[Album]:
    """List all demo albums."""
    return catalog_service.list_albums()
