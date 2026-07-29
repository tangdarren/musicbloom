"""Version 1 API schema exports for the demo catalog."""

from musicbloom.models.catalog import (
    Album,
    Artist,
    PaginatedTrackResponse,
    Track,
)

__all__ = [
    "Album",
    "Artist",
    "PaginatedTrackResponse",
    "Track",
]
