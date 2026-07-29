"""Unit tests for the demo catalog repository."""

from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.demo_data import DEMO_TRACKS


def test_repository_returns_all_artists() -> None:
    repository = DemoCatalogRepository()
    artists = repository.list_artists()

    assert len(artists) == 7
    assert artists[0].id == "artist-petal-pine"


def test_repository_returns_all_albums() -> None:
    repository = DemoCatalogRepository()
    albums = repository.list_albums()

    assert len(albums) == 7
    assert albums[0].id == "album-greenhouse-echoes"


def test_repository_returns_all_tracks() -> None:
    repository = DemoCatalogRepository()
    tracks = repository.list_tracks()

    assert len(tracks) == len(DEMO_TRACKS)


def test_repository_get_track_returns_match() -> None:
    repository = DemoCatalogRepository()
    track = repository.get_track("demo-track-001")

    assert track is not None
    assert track.title == "Morning Dew Waltz"


def test_repository_get_track_returns_none_for_unknown_id() -> None:
    repository = DemoCatalogRepository()
    assert repository.get_track("missing-track") is None
