"""Tests for Recent Blooms listening history API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.repositories.listening_event import ListeningEventRepository

TRACK_ID = "demo-track-001"
COMPLETION_POSITION_MS = 166_000


def _post_event(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/v1/listening/events", json=payload)
    assert response.status_code == 200
    return response.json()


def test_recent_blooms_empty_for_new_user(client: TestClient) -> None:
    response = client.get("/api/v1/history/recent")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_recent_blooms_skips_unknown_tracks(
    client: TestClient,
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    ListeningEventRepository(db_session).add_event(
        user_id=user.id,
        track_id="missing-track",
        event_type="started",
        idempotency_key="history-missing-track",
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "history-known-start",
        },
    )

    response = client.get("/api/v1/history/recent")

    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["track_id"] != "missing-track" for item in items)
    assert any(item["track_id"] == TRACK_ID for item in items)


def test_recent_blooms_returns_enriched_history_newest_first(
    client: TestClient,
) -> None:
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "history-start",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "progress",
            "position_ms": 60_000,
            "idempotency_key": "history-progress",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "completed",
            "position_ms": COMPLETION_POSITION_MS,
            "idempotency_key": "history-complete",
        },
    )
    _post_event(
        client,
        {
            "track_id": "demo-track-002",
            "event_type": "skipped",
            "position_ms": 12_000,
            "idempotency_key": "history-skip",
        },
    )

    response = client.get("/api/v1/history/recent")
    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]

    assert len(items) == 3
    assert [item["listening_status"] for item in items] == [
        "skipped",
        "completed",
        "played",
    ]
    assert items[0]["track_id"] == "demo-track-002"
    assert items[1]["title"] == "Morning Dew Waltz"
    assert items[1]["artist_name"] == "Petal & Pine"
    assert items[1]["artwork"]["local_path"]
    assert "occurred_at" in items[1]
    assert all(item["listening_status"] != "progress" for item in items)


def test_recent_blooms_respects_limit(client: TestClient) -> None:
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "history-limit-start",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "completed",
            "position_ms": COMPLETION_POSITION_MS,
            "idempotency_key": "history-limit-complete",
        },
    )

    response = client.get("/api/v1/history/recent?limit=1")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["listening_status"] == "completed"
