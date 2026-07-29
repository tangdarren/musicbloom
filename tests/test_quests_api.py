"""Tests for quest and achievement API endpoints."""


from fastapi.testclient import TestClient

TRACK_ID = "demo-track-001"
COMPLETION_POSITION_MS = 166_000


def _post_event(client: TestClient, payload: dict) -> None:
    response = client.post("/api/v1/listening/events", json=payload)
    assert response.status_code == 200


def test_list_quests_and_achievements(client: TestClient) -> None:
    quests = client.get("/api/v1/quests")
    achievements = client.get("/api/v1/achievements")

    assert quests.status_code == 200
    assert achievements.status_code == 200
    assert len(quests.json()) == 6
    assert len(achievements.json()) == 2


def test_complete_and_claim_first_bloom_achievement(client: TestClient) -> None:
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "started",
            "position_ms": 0,
            "idempotency_key": "quest-api-start",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "progress",
            "position_ms": 60_000,
            "idempotency_key": "quest-api-progress",
        },
    )
    _post_event(
        client,
        {
            "track_id": TRACK_ID,
            "event_type": "completed",
            "position_ms": COMPLETION_POSITION_MS,
            "idempotency_key": "quest-api-complete",
        },
    )

    achievements = client.get("/api/v1/achievements").json()
    first_bloom = next(
        item
        for item in achievements
        if item["achievement"]["id"] == "achievement-first-bloom"
    )
    assert first_bloom["status"] == "completed"

    claim = client.post("/api/v1/achievements/achievement-first-bloom/claim")
    assert claim.status_code == 200
    assert claim.json()["decoration_unlocked"]["id"] == "decoration-sprout-003"

    rewards = client.get("/api/v1/rewards")
    assert rewards.status_code == 200
    assert rewards.json()["total_claims"] == 1


def test_claim_incomplete_quest_returns_conflict(client: TestClient) -> None:
    response = client.post("/api/v1/quests/daily-complete-three-tracks/claim")

    assert response.status_code == 409
