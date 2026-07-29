"""Garden API schemas."""

from musicbloom.models.garden import (
    DecorationCatalogEntry,
    EquipDecorationResult,
    GardenState,
)

GardenStateResponse = GardenState
DecorationCatalogResponse = list[DecorationCatalogEntry]
EquipDecorationResponse = EquipDecorationResult
