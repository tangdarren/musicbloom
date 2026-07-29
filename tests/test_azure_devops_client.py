"""Tests for Azure DevOps HTTP client."""

import asyncio

import httpx
import pytest

from musicbloom.integrations.azure_devops.client import (
    HttpAzureDevOpsClient,
    sanitize_azure_devops_error_message,
)


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


def _build_transport(*, fail_times: int = 0) -> httpx.MockTransport:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "/pipelines/42/runs" in request.url.path:
            if attempts["count"] < fail_times:
                attempts["count"] += 1
                return httpx.Response(503)
            return httpx.Response(200, json=_runs_payload())
        if request.url.path.endswith("/pipelines/42"):
            return httpx.Response(200, json=_pipeline_payload())
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_get_pipeline_and_runs_return_payloads() -> None:
    client = HttpAzureDevOpsClient(transport=_build_transport())

    async def run() -> None:
        pipeline = await client.get_pipeline(
            organization="demo-org",
            project="musicbloom",
            pipeline_id=42,
            api_version="7.1",
            personal_access_token="secret-pat",
        )
        runs = await client.list_pipeline_runs(
            organization="demo-org",
            project="musicbloom",
            pipeline_id=42,
            api_version="7.1",
            personal_access_token="secret-pat",
            limit=3,
        )
        assert pipeline["name"] == "musicbloom-ci"
        assert runs["count"] == 1

    asyncio.run(run())


def test_client_retries_temporary_failures() -> None:
    client = HttpAzureDevOpsClient(transport=_build_transport(fail_times=1))

    async def run() -> None:
        runs = await client.list_pipeline_runs(
            organization="demo-org",
            project="musicbloom",
            pipeline_id=42,
            api_version="7.1",
            personal_access_token="secret-pat",
            limit=1,
        )
        assert runs["count"] == 1

    asyncio.run(run())


def test_get_playback_state_rejects_non_object_payload() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not-an-object"])

    client = HttpAzureDevOpsClient(transport=httpx.MockTransport(handler))

    async def run() -> None:
        with pytest.raises(TypeError, match="response was not an object"):
            await client.get_pipeline(
                organization="demo-org",
                project="musicbloom",
                pipeline_id=42,
                api_version="7.1",
                personal_access_token="secret-pat",
            )

    asyncio.run(run())


def test_client_retries_network_errors() -> None:
    attempts = {"count": 0}

    class FlakyTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if attempts["count"] == 0:
                attempts["count"] += 1
                raise httpx.ConnectError("network down", request=request)
            return httpx.Response(200, json=_pipeline_payload())

    client = HttpAzureDevOpsClient(transport=FlakyTransport())

    async def run() -> None:
        payload = await client.get_pipeline(
            organization="demo-org",
            project="musicbloom",
            pipeline_id=42,
            api_version="7.1",
            personal_access_token="secret-pat",
        )
        assert payload["id"] == 42

    asyncio.run(run())


def test_sanitize_azure_devops_error_message_redacts_pat() -> None:
    message = sanitize_azure_devops_error_message(
        "Authorization failed for secret-pat",
        personal_access_token="secret-pat",
    )
    assert "secret-pat" not in message
    assert "[REDACTED]" in message
