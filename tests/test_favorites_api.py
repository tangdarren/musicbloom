"""Tests for favorite tracks API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.repositories.favorite_track import FavoriteTrackRepository

TRACK_ID = "demo-track-001"
OTHER_TRACK_ID = "demo-track-002"


def test_list_favorites_empty(client: TestClient) -> None:
    response = client.get("/api/v1/favorites")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_favorites_skips_unknown_tracks(
    client: TestClient,
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    FavoriteTrackRepository(db_session).add(
        user_id=user.id,
        track_id="missing-track",
    )
    client.put(f"/api/v1/favorites/{TRACK_ID}")

    response = client.get("/api/v1/favorites")

    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["track_id"] != "missing-track" for item in items)
    assert any(item["track_id"] == TRACK_ID for item in items)


def test_add_favorite_returns_enriched_track(client: TestClient) -> None:
    response = client.put(f"/api/v1/favorites/{TRACK_ID}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["track_id"] == TRACK_ID
    assert payload["title"] == "Morning Dew Waltz"
    assert payload["artist_name"] == "Petal & Pine"
    assert payload["artwork"]["local_path"]
    assert payload["playable_in_demo_mode"] is True
    assert "favorited_at" in payload

    listed = client.get("/api/v1/favorites")
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["track_id"] == TRACK_ID


def test_add_favorite_is_idempotent(client: TestClient) -> None:
    first = client.put(f"/api/v1/favorites/{TRACK_ID}")
    second = client.put(f"/api/v1/favorites/{TRACK_ID}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["track_id"] == second.json()["track_id"]

    listed = client.get("/api/v1/favorites")
    assert len(listed.json()["items"]) == 1


def test_remove_favorite_and_repeat_is_safe(client: TestClient) -> None:
    client.put(f"/api/v1/favorites/{TRACK_ID}")

    first_delete = client.delete(f"/api/v1/favorites/{TRACK_ID}")
    second_delete = client.delete(f"/api/v1/favorites/{TRACK_ID}")

    assert first_delete.status_code == 204
    assert second_delete.status_code == 204
    assert client.get("/api/v1/favorites").json() == {"items": []}


def test_favorites_ordered_newest_first(client: TestClient) -> None:
    client.put(f"/api/v1/favorites/{TRACK_ID}")
    client.put(f"/api/v1/favorites/{OTHER_TRACK_ID}")

    items = client.get("/api/v1/favorites").json()["items"]
    assert [item["track_id"] for item in items] == [OTHER_TRACK_ID, TRACK_ID]


def test_favorite_unknown_track_returns_404(client: TestClient) -> None:
    response = client.put("/api/v1/favorites/missing-track")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
