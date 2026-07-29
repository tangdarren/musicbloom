"""Additional Azure DevOps coverage tests."""

import asyncio

import httpx
import pytest
from pydantic import SecretStr

from musicbloom.config import Settings
from musicbloom.integrations.azure_devops.client import HttpAzureDevOpsClient
from musicbloom.services.devops import (
    DevOpsService,
    _normalize_branch_ref,
    _normalize_result,
    _normalize_status,
    _parse_build_url,
    _parse_datetime,
    _parse_pipeline_name,
    _parse_run_item,
    _parse_runs,
    _parse_source_branch,
)
from musicbloom.services.devops_errors import DevOpsNotConfiguredError


def _devops_settings(**overrides: object) -> Settings:
    base = {
        "secret_key": SecretStr("development-secret-key-for-tests!!"),
        "azure_devops_org": "demo-org",
        "azure_devops_project": "musicbloom",
        "azure_devops_pipeline_id": 42,
        "azure_devops_pat": SecretStr("secret-pat"),
        "azure_devops_demo_mode": False,
        "azure_devops_status_cache_seconds": 0,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_parser_helpers_cover_edge_cases() -> None:
    assert _normalize_status("inProgress") == "in_progress"
    assert _normalize_status(None) == "unknown"
    assert _normalize_result(None) == "none"
    assert _normalize_result("partiallySucceeded") == "partially_succeeded"
    assert _parse_datetime("2026-07-28T18:00:00Z") is not None
    assert _parse_datetime("bad") is None
    assert _parse_build_url("https://example.com") == "https://example.com"
    assert _parse_build_url(None) is None
    assert _normalize_branch_ref("refs/heads/main") == "main"
    assert _parse_pipeline_name({}, 42) == "pipeline-42"
    assert _parse_runs({"value": "bad"}, pipeline_id=42, pipeline_name="ci") == []
    assert _parse_run_item("bad", pipeline_id=42, pipeline_name="ci") is None
    assert (
        _parse_source_branch(
            {
                "resources": {
                    "repositories": {
                        "self": {"refName": "refs/heads/feature/dev-garden"},
                    },
                },
            },
        )
        == "feature/dev-garden"
    )


def test_empty_runs_snapshot_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/pipelines/42/runs" in request.url.path:
            return httpx.Response(200, json={"count": 0, "value": []})
        if request.url.path.endswith("/pipelines/42"):
            return httpx.Response(200, json={"id": 42, "name": "musicbloom-ci"})
        return httpx.Response(404)

    service = DevOpsService(
        settings=_devops_settings(),
        client=HttpAzureDevOpsClient(transport=httpx.MockTransport(handler)),
    )

    snapshot = asyncio.run(service.get_status())

    assert snapshot.latest_run is None
    assert snapshot.message is not None


def test_missing_org_raises_not_configured() -> None:
    service = DevOpsService(
        settings=_devops_settings(
            azure_devops_demo_mode=False,
            demo_mode=False,
            azure_devops_org="",
        ),
        client=HttpAzureDevOpsClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    with pytest.raises(DevOpsNotConfiguredError, match="org"):
        asyncio.run(service.list_runs())


def test_client_rate_limit_retry_exhaustion() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "1"})

    client = HttpAzureDevOpsClient(transport=httpx.MockTransport(handler))

    async def run() -> None:
        with pytest.raises(httpx.HTTPStatusError):
            await client.list_pipeline_runs(
                organization="demo-org",
                project="musicbloom",
                pipeline_id=42,
                api_version="7.1",
                personal_access_token="secret-pat",
                limit=1,
            )

    asyncio.run(run())


def test_client_maps_unknown_http_status_to_api_error() -> None:
    service = DevOpsService(
        settings=_devops_settings(),
        client=HttpAzureDevOpsClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(418)),
        ),
    )

    with pytest.raises(Exception, match="418"):
        asyncio.run(service.list_runs())


def test_demo_provider_list_runs() -> None:
    from musicbloom.integrations.azure_devops.demo_provider import (
        DemoDevOpsPipelineProvider,
    )

    snapshot = DemoDevOpsPipelineProvider().list_runs(limit=2)

    assert snapshot.demo_mode is True
    assert len(snapshot.runs) == 2


def test_demo_mode_list_runs_via_service() -> None:
    service = DevOpsService(
        settings=_devops_settings(azure_devops_demo_mode=True),
        client=HttpAzureDevOpsClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    snapshot = asyncio.run(service.list_runs())

    assert snapshot.demo_mode is True
    assert len(snapshot.runs) >= 1


def test_missing_pipeline_id_raises_not_configured() -> None:
    service = DevOpsService(
        settings=_devops_settings(
            azure_devops_pipeline_id=None,
            azure_devops_demo_mode=False,
            demo_mode=False,
        ),
        client=HttpAzureDevOpsClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    with pytest.raises(DevOpsNotConfiguredError, match="pipeline ID"):
        asyncio.run(service.list_runs())


def test_parser_helpers_cover_remaining_branches() -> None:
    assert _normalize_status(123) == "unknown"
    assert _normalize_result(123) == "unknown"
    assert _parse_datetime("") is None
    assert _parse_datetime("2026-07-28T18:00:00") is not None
    assert _parse_source_branch({"resources": {"repositories": "bad"}}) is None
    assert _parse_source_branch({"resources": {}}) is None
    assert (
        _parse_source_branch(
            {"resources": {"repositories": {"self": {"refName": "main"}}}},
        )
        == "main"
    )
    assert (
        _parse_source_branch(
            {"resources": {"repositories": {"self": {"refName": "   "}}}},
        )
        is None
    )

    run_without_pipeline_object = _parse_run_item(
        {"id": 101, "name": "run"},
        pipeline_id=42,
        pipeline_name="ci",
    )
    assert run_without_pipeline_object is not None
    assert run_without_pipeline_object.pipeline_name == "ci"

    run_without_nested_pipeline = _parse_run_item(
        {
            "id": 100,
            "name": "run",
            "pipeline": {},
        },
        pipeline_id=42,
        pipeline_name="ci",
    )
    assert run_without_nested_pipeline is not None
    assert run_without_nested_pipeline.pipeline_name == "ci"

    run = _parse_run_item(
        {
            "id": 99,
            "name": "run-name",
            "state": "queued",
            "result": "succeeded",
            "pipeline": {"id": "bad", "name": 123},
            "resources": {
                "repositories": {
                    "self": "not-a-dict",
                    "empty": {},
                    "other": {"refName": "refs/heads/main"},
                },
            },
        },
        pipeline_id=42,
        pipeline_name="ci",
    )
    assert run is not None
    assert run.pipeline_id == 42
    assert run.source_branch == "main"

    invalid_run = _parse_run_item(
        {"id": "bad", "name": "run"},
        pipeline_id=1,
        pipeline_name="x",
    )
    assert invalid_run is None
    assert _parse_runs({"value": [{}]}, pipeline_id=1, pipeline_name="x") == []


def test_resolved_azure_devops_pat_ignores_blank_values() -> None:
    settings = Settings(azure_devops_pat=SecretStr("   "))
    assert settings.resolved_azure_devops_pat is None


def test_client_raises_when_retry_loop_exits_without_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(HttpAzureDevOpsClient, "_MAX_RETRIES", -1)
    client = HttpAzureDevOpsClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
    )

    async def run() -> None:
        with pytest.raises(RuntimeError, match="request failed"):
            await client.get_pipeline(
                organization="demo-org",
                project="musicbloom",
                pipeline_id=42,
                api_version="7.1",
                personal_access_token="secret-pat",
            )

    asyncio.run(run())
