"""API tests for the player session endpoints."""

from fastapi.testclient import TestClient

from musicbloom.api.app import app

client = TestClient(app)


def test_get_player_returns_initial_session() -> None:
    response = client.get("/api/v1/player")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "stopped"
    assert data["active_track"] is None
    assert data["queue"] == []
    assert data["volume"]["level"] == 0.8


def test_play_track_starts_session() -> None:
    response = client.put("/api/v1/player/play", json={"track_id": "demo-track-001"})

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "playing"
    assert data["active_track"]["track_id"] == "demo-track-001"


def test_play_without_body_resumes_or_starts_queue() -> None:
    client.post("/api/v1/player/queue", json={"track_id": "demo-track-002"})
    response = client.put("/api/v1/player/play")

    assert response.status_code == 200
    assert response.json()["active_track"]["track_id"] == "demo-track-002"


def test_play_unknown_track_returns_404() -> None:
    response = client.put(
        "/api/v1/player/play",
        json={"track_id": "missing-track"},
    )

    assert response.status_code == 404


def test_play_non_playable_track_returns_400() -> None:
    response = client.put(
        "/api/v1/player/play",
        json={"track_id": "demo-track-008"},
    )

    assert response.status_code == 400


def test_pause_active_track() -> None:
    client.put("/api/v1/player/play", json={"track_id": "demo-track-001"})
    response = client.put("/api/v1/player/pause")

    assert response.status_code == 200
    assert response.json()["state"] == "paused"


def test_pause_without_active_track_returns_409() -> None:
    response = client.put("/api/v1/player/pause")

    assert response.status_code == 409


def test_seek_updates_position() -> None:
    client.put("/api/v1/player/play", json={"track_id": "demo-track-001"})
    response = client.put("/api/v1/player/seek", json={"position_ms": 30_000})

    assert response.status_code == 200
    assert response.json()["active_track"]["position"]["position_ms"] == 30_000


def test_seek_beyond_duration_returns_400() -> None:
    client.put("/api/v1/player/play", json={"track_id": "demo-track-001"})
    response = client.put("/api/v1/player/seek", json={"position_ms": 999_999})

    assert response.status_code == 400


def test_seek_rejects_invalid_payload() -> None:
    client.put("/api/v1/player/play", json={"track_id": "demo-track-001"})
    response = client.put("/api/v1/player/seek", json={"position_ms": -1})

    assert response.status_code == 422


def test_set_volume() -> None:
    response = client.put("/api/v1/player/volume", json={"level": 0.35})

    assert response.status_code == 200
    assert response.json()["volume"]["level"] == 0.35


def test_set_volume_rejects_invalid_payload() -> None:
    response = client.put("/api/v1/player/volume", json={"level": 2.0})

    assert response.status_code == 422


def test_set_shuffle_and_repeat() -> None:
    shuffle = client.put("/api/v1/player/shuffle", json={"enabled": True})
    repeat = client.put("/api/v1/player/repeat", json={"mode": "all"})

    assert shuffle.status_code == 200
    assert shuffle.json()["shuffle"] is True
    assert repeat.status_code == 200
    assert repeat.json()["repeat_mode"] == "all"


def test_add_to_queue() -> None:
    response = client.post(
        "/api/v1/player/queue",
        json={"track_id": "demo-track-003"},
    )

    assert response.status_code == 200
    assert len(response.json()["queue"]) == 1


def test_add_duplicate_queue_item_returns_409() -> None:
    client.post("/api/v1/player/queue", json={"track_id": "demo-track-003"})
    response = client.post(
        "/api/v1/player/queue",
        json={"track_id": "demo-track-003"},
    )

    assert response.status_code == 409


def test_add_duplicate_when_allowed() -> None:
    client.post("/api/v1/player/queue", json={"track_id": "demo-track-003"})
    response = client.post(
        "/api/v1/player/queue",
        json={"track_id": "demo-track-003", "allow_duplicate": True},
    )

    assert response.status_code == 200
    assert len(response.json()["queue"]) == 2


def test_remove_from_queue() -> None:
    client.post("/api/v1/player/queue", json={"track_id": "demo-track-003"})
    response = client.delete("/api/v1/player/queue/demo-track-003")

    assert response.status_code == 200
    assert response.json()["queue"] == []


def test_remove_missing_queue_item_returns_404() -> None:
    response = client.delete("/api/v1/player/queue/demo-track-003")

    assert response.status_code == 404


def test_next_and_previous_navigation() -> None:
    client.post("/api/v1/player/queue", json={"track_id": "demo-track-001"})
    client.post("/api/v1/player/queue", json={"track_id": "demo-track-002"})
    client.put("/api/v1/player/play")

    next_response = client.post("/api/v1/player/next")
    assert next_response.status_code == 200
    assert next_response.json()["active_track"]["track_id"] == "demo-track-002"

    previous_response = client.post("/api/v1/player/previous")
    assert previous_response.status_code == 200
    assert previous_response.json()["active_track"]["track_id"] == "demo-track-001"


def test_next_on_empty_session_returns_409() -> None:
    response = client.post("/api/v1/player/next")

    assert response.status_code == 409


def test_play_while_already_playing_is_idempotent() -> None:
    client.put("/api/v1/player/play", json={"track_id": "demo-track-001"})
    response = client.put("/api/v1/player/play")

    assert response.status_code == 200
    assert response.json()["state"] == "playing"


def test_pause_when_already_paused_is_idempotent() -> None:
    client.put("/api/v1/player/play", json={"track_id": "demo-track-001"})
    client.put("/api/v1/player/pause")
    response = client.put("/api/v1/player/pause")

    assert response.status_code == 200
    assert response.json()["state"] == "paused"


def test_previous_on_empty_session_returns_409() -> None:
    response = client.post("/api/v1/player/previous")

    assert response.status_code == 409


def test_seek_without_active_track_returns_409() -> None:
    response = client.put("/api/v1/player/seek", json={"position_ms": 1_000})

    assert response.status_code == 409


def test_player_endpoints_have_openapi_metadata() -> None:
    schema = app.openapi()
    paths = schema["paths"]

    assert "/api/v1/player" in paths
    assert paths["/api/v1/player"]["get"]["summary"] == "Get player session"
    assert "/api/v1/player/play" in paths
    assert "/api/v1/player/queue/{track_id}" in paths
