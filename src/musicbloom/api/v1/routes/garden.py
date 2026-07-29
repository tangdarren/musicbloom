"""Garden routes."""

from fastapi import APIRouter, Response, status

from musicbloom.api.v1.schemas.garden import (
    DecorationCatalogResponse,
    EquipDecorationResponse,
    GardenStateResponse,
)
from musicbloom.dependencies import GardenServiceDep

router = APIRouter(tags=["garden"])


@router.get(
    "/garden",
    response_model=GardenStateResponse,
    summary="Get garden state",
    description=(
        "Return the interactive garden snapshot derived from real listening "
        "progress, decorations, and achievements."
    ),
)
def get_garden(garden_service: GardenServiceDep) -> GardenStateResponse:
    """Return the current user's garden state."""
    return garden_service.get_garden_state()


@router.get(
    "/decorations",
    response_model=DecorationCatalogResponse,
    summary="List decorations",
    description="Return the decoration catalog with unlock and equip status.",
)
def list_decorations(
    garden_service: GardenServiceDep,
) -> DecorationCatalogResponse:
    """Return decorations for the current user."""
    return garden_service.list_decorations()


@router.put(
    "/garden/decorations/{decoration_id}/equip",
    response_model=EquipDecorationResponse,
    summary="Equip a decoration",
    description="Equip an unlocked decoration in its default garden slot.",
)
def equip_decoration(
    decoration_id: str,
    garden_service: GardenServiceDep,
) -> EquipDecorationResponse:
    """Equip an unlocked decoration."""
    return garden_service.equip_decoration(decoration_id)


@router.delete(
    "/garden/decorations/{decoration_id}/equip",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unequip a decoration",
    description="Remove a decoration from the garden.",
)
def unequip_decoration(
    decoration_id: str,
    garden_service: GardenServiceDep,
) -> Response:
    """Unequip a decoration."""
    garden_service.unequip_decoration(decoration_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
