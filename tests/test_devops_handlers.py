"""Tests for Azure DevOps exception handlers."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from musicbloom.api.v1.devops_handlers import register_devops_exception_handlers
from musicbloom.services.devops_errors import DevOpsAuthenticationError


def test_devops_exception_handler_returns_status_code() -> None:
    app = FastAPI()
    register_devops_exception_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise DevOpsAuthenticationError("bad token")

    client = TestClient(app)
    response = client.get("/boom")

    assert response.status_code == 401
    assert response.json() == {"detail": "bad token"}
