"""Tests for Azure DevOps API endpoints."""

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from musicbloom.config import Settings
from musicbloom.dependencies import get_azure_devops_client, get_settings


def _devops_settings(**overrides: object) -> Settings:
    base = {
        "secret_key": SecretStr("development-secret-key-for-tests!!"),
        "azure_devops_org": "demo-org",
        "azure_devops_project": "musicbloom",
        "azure_devops_pipeline_id": 42,
        "azure_devops_pat": SecretStr("secret-pat"),
        "azure_devops_demo_mode": False,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def _build_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/pipelines/42/runs" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "count": 1,
                    "value": [
                        {
                            "id": 1284,
                            "name": "20260728.42",
                            "state": "completed",
                            "result": "succeeded",
                            "createdDate": "2026-07-28T18:00:00Z",
                            "finishedDate": "2026-07-28T18:06:00Z",
                            "url": (
                                "https://dev.azure.com/demo-org/musicbloom/"
                                "_build/results?buildId=1284"
                            ),
                            "pipeline": {"id": 42, "name": "musicbloom-ci"},
                        },
                    ],
                },
            )
        if request.url.path.endswith("/pipelines/42"):
            return httpx.Response(200, json={"id": 42, "name": "musicbloom-ci"})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.fixture
def devops_client(test_app) -> None:
    from musicbloom.integrations.azure_devops.client import HttpAzureDevOpsClient

    get_settings.cache_clear()
    test_app.dependency_overrides[get_settings] = lambda: _devops_settings()
    test_app.dependency_overrides[get_azure_devops_client] = (
        lambda: HttpAzureDevOpsClient(transport=_build_transport())
    )
    yield
    test_app.dependency_overrides.pop(get_settings, None)
    test_app.dependency_overrides.pop(get_azure_devops_client, None)
    get_settings.cache_clear()


def test_get_devops_status(client: TestClient, devops_client: None) -> None:
    response = client.get("/api/v1/devops/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["latest_run"]["run_name"] == "20260728.42"
    assert "secret-pat" not in response.text


def test_list_devops_runs(client: TestClient, devops_client: None) -> None:
    response = client.get("/api/v1/devops/runs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pipeline_name"] == "musicbloom-ci"
    assert len(payload["runs"]) == 1


def test_devops_demo_mode_without_credentials(client: TestClient, test_app) -> None:
    get_settings.cache_clear()
    test_app.dependency_overrides[get_settings] = lambda: Settings(
        demo_mode=True,
        azure_devops_demo_mode=True,
    )

    response = client.get("/api/v1/devops/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["demo_mode"] is True
    assert payload["configured"] is False

    test_app.dependency_overrides.pop(get_settings, None)
    get_settings.cache_clear()
