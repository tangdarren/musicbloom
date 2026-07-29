"""Tests for progression exception handlers."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from musicbloom.api.v1.progression_handlers import (
    register_progression_exception_handlers,
)
from musicbloom.services.progression_errors import InvalidListeningEventError


def test_progression_exception_handler_returns_service_status_code() -> None:
    app = FastAPI()
    register_progression_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise InvalidListeningEventError("bad event")

    client = TestClient(app)
    response = client.get("/boom")

    assert response.status_code == 400
    assert response.json()["detail"] == "bad event"
