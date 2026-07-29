"""In-memory demo catalog repository."""

from musicbloom.models.catalog import Album, Artist, Track
from musicbloom.repositories.demo_data import DEMO_ALBUMS, DEMO_ARTISTS, DEMO_TRACKS


class DemoCatalogRepository:
    """Read-only repository backed by deterministic demo seed data."""

    def __init__(
        self,
        artists: tuple[Artist, ...] = DEMO_ARTISTS,
        albums: tuple[Album, ...] = DEMO_ALBUMS,
        tracks: tuple[Track, ...] = DEMO_TRACKS,
    ) -> None:
        self._artists = artists
        self._albums = albums
        self._tracks = tracks

    def list_artists(self) -> list[Artist]:
        """Return all demo artists in catalog order."""
        return list(self._artists)

    def list_albums(self) -> list[Album]:
        """Return all demo albums in catalog order."""
        return list(self._albums)

    def list_tracks(self) -> list[Track]:
        """Return all demo tracks in catalog order."""
        return list(self._tracks)

    def get_track(self, track_id: str) -> Track | None:
        """Return a demo track by stable identifier."""
        for track in self._tracks:
            if track.id == track_id:
                return track
        return None
