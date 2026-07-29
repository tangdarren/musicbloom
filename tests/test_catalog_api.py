"""API tests for the demo music catalog."""

from fastapi.testclient import TestClient

from musicbloom.api.app import app
from musicbloom.repositories.demo_data import DEMO_TRACKS

client = TestClient(app)


def test_list_tracks_returns_paginated_catalog() -> None:
    response = client.get("/api/v1/tracks?page=1&page_size=3")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(DEMO_TRACKS)
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["id"] == "demo-track-001"


def test_list_tracks_includes_required_track_fields() -> None:
    response = client.get("/api/v1/tracks?page=1&page_size=1")
    track = response.json()["items"][0]

    assert track["title"] == "Morning Dew Waltz"
    assert track["artist_name"] == "Petal & Pine"
    assert track["album_title"] == "Greenhouse Echoes"
    assert track["duration_ms"] == 184_000
    artwork_path = track["artwork"]["local_path"]
    assert artwork_path == "/static/demo/artwork/morning-dew-waltz.png"
    assert track["audio"]["local_path"] == "/static/demo/audio/morning-dew-waltz.ogg"
    assert track["mood"] == "calm"
    assert track["genre"] == "acoustic garden"
    assert track["accent_theme"]["primary"] == "#7BC47F"
    assert track["playable_in_demo_mode"] is True


def test_list_tracks_filter_by_artist() -> None:
    response = client.get("/api/v1/tracks?artist=Verdant")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Fern Fanfare"


def test_list_tracks_filter_by_album() -> None:
    response = client.get("/api/v1/tracks?album=April")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_tracks_filter_by_genre() -> None:
    response = client.get("/api/v1/tracks?genre=chiptune")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_tracks_filter_by_mood() -> None:
    response = client.get("/api/v1/tracks?mood=dreamy")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Starlit Sprinkler"


def test_list_tracks_rejects_invalid_page() -> None:
    response = client.get("/api/v1/tracks?page=0")

    assert response.status_code == 422


def test_list_tracks_rejects_invalid_page_size() -> None:
    response = client.get("/api/v1/tracks?page_size=0")

    assert response.status_code == 422


def test_list_tracks_rejects_page_size_above_limit() -> None:
    response = client.get("/api/v1/tracks?page_size=101")

    assert response.status_code == 422


def test_get_track_returns_track() -> None:
    response = client.get("/api/v1/tracks/demo-track-002")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Sunbeam Carousel"
    assert data["audio"]["url"] == "https://demo.musicbloom.local/audio/sunbeam-carousel.ogg"


def test_get_track_returns_404_for_unknown_track() -> None:
    response = client.get("/api/v1/tracks/not-a-real-track")

    assert response.status_code == 404
    assert response.json()["detail"] == "Track 'not-a-real-track' was not found"


def test_get_non_playable_demo_track() -> None:
    response = client.get("/api/v1/tracks/demo-track-008")

    assert response.status_code == 200
    assert response.json()["playable_in_demo_mode"] is False
    assert response.json()["mood"] == "mysterious"


def test_list_artists_returns_catalog() -> None:
    response = client.get("/api/v1/artists")

    assert response.status_code == 200
    artists = response.json()
    assert len(artists) == 7
    assert artists[0]["id"] == "artist-petal-pine"
    assert artists[0]["name"] == "Petal & Pine"
    assert artists[0]["genre"] == "acoustic garden"


def test_list_albums_returns_catalog() -> None:
    response = client.get("/api/v1/albums")

    assert response.status_code == 200
    albums = response.json()
    assert len(albums) == 7
    assert albums[0]["title"] == "Greenhouse Echoes"
    artwork_path = albums[0]["artwork"]["local_path"]
    assert artwork_path == "/static/demo/artwork/greenhouse-echoes.png"


def test_catalog_endpoints_have_openapi_metadata() -> None:
    schema = app.openapi()
    paths = schema["paths"]

    assert "/api/v1/tracks" in paths
    assert paths["/api/v1/tracks"]["get"]["summary"] == "List demo tracks"
    assert "/api/v1/tracks/{track_id}" in paths
    assert "/api/v1/artists" in paths
    assert "/api/v1/albums" in paths
