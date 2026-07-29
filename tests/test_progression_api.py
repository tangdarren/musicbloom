"""Tests for progression API endpoints."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

TRACK_ID = "demo-track-001"
COMPLETION_POSITION_MS = 166_000


def _post_event(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/v1/listening/events", json=payload)
    assert response.status_code == 200
    return response.json()


def test_progress_endpoints_return_initial_state(client: TestClient) -> None:
    progress = client.get("/api/v1/progress")
    stats = client.get("/api/v1/stats")
    streak = client.get("/api/v1/streak")

    assert progress.status_code == 200
    assert stats.status_code == 200
    assert streak.status_code == 200
    assert progress.json()["melody_points"] == 0
    assert stats.json()["total_listening_events"] == 0
    assert streak.json()["current_days"] == 0


def test_listening_event_flow_awards_completion_bonus(client: TestClient) -> None:
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "api-start",
        },
    )
    progress = _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "progress",
            "position_ms": 60_000,
            "idempotency_key": "api-progress",
        },
    )
    completed = _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "completed",
            "position_ms": COMPLETION_POSITION_MS,
            "idempotency_key": "api-complete",
        },
    )

    assert progress["melody_points_earned"] > 0
    assert any(
        award["reason"] == "track_completion" for award in completed["awards"]
    )
    assert client.get("/api/v1/progress").json()["melody_points"] > 0


def test_duplicate_idempotency_key_returns_duplicate_flag(client: TestClient) -> None:
    payload = {
        "track_id": TRACK_ID,
        "event_type": "started",
        "position_ms": 0,
        "idempotency_key": "api-duplicate",
    }
    first = _post_event(client, payload)
    second = _post_event(client, payload)

    assert first["duplicate"] is False
    assert second["duplicate"] is True


def test_invalid_track_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/listening/events",
        json={
            "track_id": "missing-track",
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "missing-track",
        },
    )

    assert response.status_code == 404


def test_invalid_duration_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/listening/events",
        json={
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 999_999,
            "idempotency_key": "invalid-duration",
        },
    )

    assert response.status_code == 400


def test_skipped_track_cannot_be_completed(client: TestClient) -> None:
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "api-skip-start",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "skipped",
            "position_ms": 30_000,
            "idempotency_key": "api-skip",
        },
    )
    response = client.post(
        "/api/v1/listening/events",
        json={
            "track_id": TRACK_ID,
            "event_type": "completed",
            "position_ms": COMPLETION_POSITION_MS,
            "idempotency_key": "api-skip-complete",
        },
    )

    assert response.status_code == 400


def test_streak_endpoint_reflects_consecutive_days(client: TestClient) -> None:
    day_one = datetime(2026, 2, 1, 12, 0, 0, tzinfo=UTC)
    day_two = day_one + timedelta(days=1)

    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "api-streak-start-1",
            "occurred_at": day_one.isoformat(),
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "progress",
            "position_ms": 60_000,
            "idempotency_key": "api-streak-progress-1",
            "occurred_at": day_one.isoformat(),
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "api-streak-start-2",
            "occurred_at": day_two.isoformat(),
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "progress",
            "position_ms": 60_000,
            "idempotency_key": "api-streak-progress-2",
            "occurred_at": day_two.isoformat(),
        },
    )

    streak = client.get("/api/v1/streak").json()

    assert streak["current_days"] == 2
