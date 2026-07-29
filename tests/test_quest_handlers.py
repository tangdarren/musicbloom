"""Tests for quest exception handlers."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from musicbloom.api.v1.quest_handlers import register_quest_exception_handlers
from musicbloom.services.quest_errors import RewardNotClaimableError


def test_quest_exception_handler_returns_service_status_code() -> None:
    app = FastAPI()
    register_quest_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise RewardNotClaimableError("not ready")

    client = TestClient(app)
    response = client.get("/boom")

    assert response.status_code == 409
    assert response.json()["detail"] == "not ready"
