"""Tests for Azure DevOps pipeline service."""

import asyncio
from time import monotonic

import httpx
import pytest
from pydantic import SecretStr

from musicbloom.config import Settings
from musicbloom.integrations.azure_devops.client import HttpAzureDevOpsClient
from musicbloom.integrations.azure_devops.demo_provider import (
    DemoDevOpsPipelineProvider,
)
from musicbloom.models.devops import DevOpsRunResult, DevOpsRunStatus
from musicbloom.services.devops import DevOpsService
from musicbloom.services.devops_errors import (
    DevOpsApiError,
    DevOpsAuthenticationError,
    DevOpsAuthorizationError,
    DevOpsNotConfiguredError,
    DevOpsRateLimitedError,
)


def _devops_settings(**overrides: object) -> Settings:
    base = {
        "secret_key": SecretStr("development-secret-key-for-tests!!"),
        "azure_devops_org": "demo-org",
        "azure_devops_project": "musicbloom",
        "azure_devops_pipeline_id": 42,
        "azure_devops_pat": SecretStr("secret-pat"),
        "azure_devops_demo_mode": False,
        "azure_devops_recent_run_limit": 3,
        "azure_devops_status_cache_seconds": 30,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def _pipeline_payload() -> dict[str, object]:
    return {"id": 42, "name": "musicbloom-ci"}


def _runs_payload() -> dict[str, object]:
    return {
        "count": 1,
        "value": [
            {
                "id": 1284,
                "name": "20260728.42",
                "state": "completed",
                "result": "succeeded",
                "createdDate": "2026-07-28T18:00:00Z",
                "finishedDate": "2026-07-28T18:06:00Z",
                "url": "https://dev.azure.com/demo-org/musicbloom/_build/results?buildId=1284",
                "pipeline": {"id": 42, "name": "musicbloom-ci"},
                "resources": {
                    "repositories": {
                        "self": {"refName": "refs/heads/main"},
                    },
                },
            },
        ],
    }


def _build_transport(status_code: int | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if status_code is not None:
            return httpx.Response(status_code)
        if "/pipelines/42/runs" in request.url.path:
            return httpx.Response(200, json=_runs_payload())
        if request.url.path.endswith("/pipelines/42"):
            return httpx.Response(200, json=_pipeline_payload())
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _service(
    *,
    settings: Settings | None = None,
    transport: httpx.MockTransport | None = None,
) -> DevOpsService:
    return DevOpsService(
        settings=settings or _devops_settings(),
        client=HttpAzureDevOpsClient(
            transport=transport or _build_transport(),
            timeout_seconds=5.0,
        ),
        demo_provider=DemoDevOpsPipelineProvider(),
    )


def test_demo_mode_returns_demo_status() -> None:
    service = _service(settings=_devops_settings(azure_devops_demo_mode=True))

    snapshot = asyncio.run(service.get_status())

    assert snapshot.demo_mode is True
    assert snapshot.latest_run is not None
    assert snapshot.latest_run.result == DevOpsRunResult.SUCCEEDED


def test_live_status_normalizes_latest_run() -> None:
    service = _service()

    snapshot = asyncio.run(service.get_status())

    assert snapshot.configured is True
    assert snapshot.demo_mode is False
    assert snapshot.pipeline_name == "musicbloom-ci"
    assert snapshot.latest_run is not None
    assert snapshot.latest_run.status == DevOpsRunStatus.COMPLETED
    assert snapshot.latest_run.source_branch == "main"


def test_live_runs_respects_recent_limit() -> None:
    service = _service(settings=_devops_settings(azure_devops_recent_run_limit=1))

    runs_snapshot = asyncio.run(service.list_runs())

    assert len(runs_snapshot.runs) == 1


def test_status_cache_avoids_repeat_requests() -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if "/pipelines/42/runs" in request.url.path:
            return httpx.Response(200, json=_runs_payload())
        if request.url.path.endswith("/pipelines/42"):
            return httpx.Response(200, json=_pipeline_payload())
        return httpx.Response(404)

    service = _service(transport=httpx.MockTransport(handler))

    asyncio.run(service.get_status())
    asyncio.run(service.get_status())

    assert calls["count"] == 2


def test_missing_configuration_raises_not_configured() -> None:
    service = _service(
        settings=_devops_settings(
            azure_devops_demo_mode=False,
            demo_mode=False,
            azure_devops_pat=None,
        ),
    )

    with pytest.raises(DevOpsNotConfiguredError):
        asyncio.run(service.list_runs())


def test_authentication_failure_maps_to_401() -> None:
    service = _service(transport=_build_transport(status_code=401))

    with pytest.raises(DevOpsAuthenticationError):
        asyncio.run(service.list_runs())


def test_authorization_failure_maps_to_403() -> None:
    service = _service(transport=_build_transport(status_code=403))

    with pytest.raises(DevOpsAuthorizationError):
        asyncio.run(service.list_runs())


def test_rate_limit_maps_to_429() -> None:
    service = _service(transport=_build_transport(status_code=429))

    with pytest.raises(DevOpsRateLimitedError):
        asyncio.run(service.list_runs())


def test_server_error_maps_to_api_error() -> None:
    service = _service(transport=_build_transport(status_code=500))

    with pytest.raises(DevOpsApiError):
        asyncio.run(service.list_runs())


def test_network_error_maps_to_api_error() -> None:
    class BrokenTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("network down", request=request)

    service = DevOpsService(
        settings=_devops_settings(),
        client=HttpAzureDevOpsClient(transport=BrokenTransport(), timeout_seconds=1.0),
    )

    with pytest.raises(DevOpsApiError):
        asyncio.run(service.list_runs())


def test_expired_cache_is_refreshed(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _service(settings=_devops_settings(azure_devops_status_cache_seconds=1))
    asyncio.run(service.get_status())

    monkeypatch.setattr(
        "musicbloom.services.devops.monotonic",
        lambda: monotonic() + 5,
    )

    refreshed = asyncio.run(service.get_status())
    assert refreshed.latest_run is not None
