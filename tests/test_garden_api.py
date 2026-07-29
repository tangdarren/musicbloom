"""Tests for garden API endpoints."""

from fastapi.testclient import TestClient

TRACK_ID = "demo-track-001"
COMPLETION_POSITION_MS = 166_000


def _post_event(client: TestClient, payload: dict) -> None:
    response = client.post("/api/v1/listening/events", json=payload)
    assert response.status_code == 200


def _unlock_sprout(client: TestClient) -> None:
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "garden-api-start",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "progress",
            "position_ms": 60_000,
            "idempotency_key": "garden-api-progress",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "completed",
            "position_ms": COMPLETION_POSITION_MS,
            "idempotency_key": "garden-api-complete",
        },
    )
    claim = client.post("/api/v1/achievements/achievement-first-bloom/claim")
    assert claim.status_code == 200


def test_get_garden_for_new_user(client: TestClient) -> None:
    response = client.get("/api/v1/garden")

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["garden_name"] == "Starter Garden"
    assert payload["mood"] == "serene"
    assert payload["tracks_completed"] == 0
    assert payload["artist_flowers"] == []
    assert payload["equipped_decorations"] == []


def test_list_decorations(client: TestClient) -> None:
    response = client.get("/api/v1/decorations")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 3
    assert all(item["unlocked"] is False for item in payload)


def test_equip_locked_decoration_returns_conflict(client: TestClient) -> None:
    response = client.put("/api/v1/garden/decorations/decoration-sprout-003/equip")

    assert response.status_code == 409
    assert "locked" in response.json()["detail"].lower()


def test_equip_and_unequip_unlocked_decoration(client: TestClient) -> None:
    _unlock_sprout(client)

    equip = client.put("/api/v1/garden/decorations/decoration-sprout-003/equip")
    assert equip.status_code == 200
    assert equip.json()["slot"] == "south"

    garden = client.get("/api/v1/garden").json()
    assert len(garden["equipped_decorations"]) == 1
    assert garden["equipped_decorations"][0]["decoration"]["id"] == (
        "decoration-sprout-003"
    )

    decorations = client.get("/api/v1/decorations").json()
    sprout = next(
        item
        for item in decorations
        if item["decoration"]["id"] == "decoration-sprout-003"
    )
    assert sprout["equipped"] is True

    unequip = client.delete(
        "/api/v1/garden/decorations/decoration-sprout-003/equip",
    )
    assert unequip.status_code == 204

    garden_after = client.get("/api/v1/garden").json()
    assert garden_after["equipped_decorations"] == []


def test_unequip_missing_decoration_returns_not_found(client: TestClient) -> None:
    response = client.delete(
        "/api/v1/garden/decorations/decoration-sprout-003/equip",
    )

    assert response.status_code == 404


def test_equip_unknown_decoration_returns_not_found(client: TestClient) -> None:
    response = client.put("/api/v1/garden/decorations/missing-decoration/equip")

    assert response.status_code == 404


def test_list_decorations_after_unlock(client: TestClient) -> None:
    _unlock_sprout(client)

    decorations = client.get("/api/v1/decorations").json()
    sprout = next(
        item
        for item in decorations
        if item["decoration"]["id"] == "decoration-sprout-003"
    )
    assert sprout["unlocked"] is True


def test_garden_reflects_completed_track(client: TestClient) -> None:
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "garden-track-start",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "progress",
            "position_ms": 60_000,
            "idempotency_key": "garden-track-progress",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "completed",
            "position_ms": COMPLETION_POSITION_MS,
            "idempotency_key": "garden-track-complete",
        },
    )

    garden = client.get("/api/v1/garden").json()
    assert garden["tracks_completed"] == 1
    assert garden["mood"] == "cheerful"
    assert len(garden["artist_flowers"]) == 1
    assert garden["milestone_plants"][0]["unlocked"] is True
