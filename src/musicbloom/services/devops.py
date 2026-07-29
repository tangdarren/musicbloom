"""Azure DevOps pipeline status business logic."""

from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any

import httpx

from musicbloom.config import Settings
from musicbloom.integrations.azure_devops.client import (
    AzureDevOpsClient,
    sanitize_azure_devops_error_message,
)
from musicbloom.integrations.azure_devops.demo_provider import (
    DemoDevOpsPipelineProvider,
)
from musicbloom.models.devops import (
    DevOpsPipelineRun,
    DevOpsRunResult,
    DevOpsRunsSnapshot,
    DevOpsRunStatus,
    DevOpsStatusSnapshot,
)
from musicbloom.services.devops_errors import (
    DevOpsApiError,
    DevOpsAuthenticationError,
    DevOpsAuthorizationError,
    DevOpsNotConfiguredError,
    DevOpsRateLimitedError,
    DevOpsServiceError,
)


@dataclass(frozen=True)
class _CachedStatus:
    snapshot: DevOpsStatusSnapshot
    expires_at: float


class DevOpsService:
    """Service layer for Azure DevOps pipeline status."""

    def __init__(
        self,
        *,
        settings: Settings,
        client: AzureDevOpsClient,
        demo_provider: DemoDevOpsPipelineProvider | None = None,
    ) -> None:
        self._settings = settings
        self._client = client
        self._demo_provider = demo_provider or DemoDevOpsPipelineProvider()
        self._status_cache: _CachedStatus | None = None

    def is_configured(self) -> bool:
        """Return True when live Azure DevOps credentials are configured."""
        return self._settings.azure_devops_configured

    def uses_demo_mode(self) -> bool:
        """Return True when demo pipeline data should be served."""
        if self._settings.azure_devops_demo_mode:
            return True
        if not self.is_configured():
            return self._settings.demo_mode
        return False

    async def get_status(self) -> DevOpsStatusSnapshot:
        """Return the current pipeline health snapshot."""
        if self.uses_demo_mode():
            return self._demo_provider.get_status()

        cached = self._read_status_cache()
        if cached is not None:
            return cached

        runs_snapshot = await self._fetch_runs(limit=1)
        latest_run = runs_snapshot.runs[0] if runs_snapshot.runs else None
        snapshot = DevOpsStatusSnapshot(
            configured=True,
            demo_mode=False,
            pipeline_id=runs_snapshot.pipeline_id,
            pipeline_name=runs_snapshot.pipeline_name,
            latest_run=latest_run,
            message=(
                "Live Azure DevOps pipeline status."
                if latest_run is not None
                else "No recent pipeline runs were returned by Azure DevOps."
            ),
        )
        self._write_status_cache(snapshot)
        return snapshot

    async def list_runs(self) -> DevOpsRunsSnapshot:
        """Return recent pipeline runs."""
        if self.uses_demo_mode():
            return self._demo_provider.list_runs(
                limit=self._settings.azure_devops_recent_run_limit,
            )
        return await self._fetch_runs(
            limit=self._settings.azure_devops_recent_run_limit,
        )

    async def _fetch_runs(self, *, limit: int) -> DevOpsRunsSnapshot:
        organization = self._require_non_empty(self._settings.azure_devops_org, "org")
        project = self._require_non_empty(
            self._settings.azure_devops_project,
            "project",
        )
        pipeline_id = self._settings.azure_devops_pipeline_id
        if pipeline_id is None:
            raise DevOpsNotConfiguredError(
                "Azure DevOps pipeline ID is not configured.",
            )

        personal_access_token = self._settings.resolved_azure_devops_pat
        if personal_access_token is None:
            raise DevOpsNotConfiguredError(
                "Azure DevOps personal access token is not configured.",
            )

        api_version = self._settings.azure_devops_api_version
        try:
            pipeline_payload = await self._client.get_pipeline(
                organization=organization,
                project=project,
                pipeline_id=pipeline_id,
                api_version=api_version,
                personal_access_token=personal_access_token,
            )
            runs_payload = await self._client.list_pipeline_runs(
                organization=organization,
                project=project,
                pipeline_id=pipeline_id,
                api_version=api_version,
                personal_access_token=personal_access_token,
                limit=limit,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc, personal_access_token) from exc
        except httpx.HTTPError as exc:
            message = sanitize_azure_devops_error_message(
                "Azure DevOps request failed.",
                personal_access_token=personal_access_token,
            )
            raise DevOpsApiError(message) from exc

        pipeline_name = _parse_pipeline_name(pipeline_payload, pipeline_id)
        runs = _parse_runs(
            runs_payload,
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
        )
        return DevOpsRunsSnapshot(
            configured=True,
            demo_mode=False,
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            runs=runs[:limit],
            message="Live Azure DevOps pipeline runs.",
        )

    def _read_status_cache(self) -> DevOpsStatusSnapshot | None:
        cache_seconds = self._settings.azure_devops_status_cache_seconds
        if cache_seconds <= 0 or self._status_cache is None:
            return None
        if monotonic() >= self._status_cache.expires_at:
            self._status_cache = None
            return None
        return self._status_cache.snapshot

    def _write_status_cache(self, snapshot: DevOpsStatusSnapshot) -> None:
        cache_seconds = self._settings.azure_devops_status_cache_seconds
        if cache_seconds <= 0:
            return
        self._status_cache = _CachedStatus(
            snapshot=snapshot,
            expires_at=monotonic() + cache_seconds,
        )

    def _map_http_error(
        self,
        exc: httpx.HTTPStatusError,
        personal_access_token: str,
    ) -> DevOpsServiceError:
        status_code = exc.response.status_code
        safe_message = sanitize_azure_devops_error_message(
            f"Azure DevOps request failed with status {status_code}.",
            personal_access_token=personal_access_token,
        )
        if status_code == 401:
            return DevOpsAuthenticationError(
                "Azure DevOps authentication failed. Verify the personal access token.",
            )
        if status_code == 403:
            return DevOpsAuthorizationError(
                "Azure DevOps denied access to the configured pipeline.",
            )
        if status_code == 429:
            return DevOpsRateLimitedError(
                "Azure DevOps rate limit reached. Try again shortly.",
            )
        if status_code >= 500:
            return DevOpsApiError(
                "Azure DevOps is temporarily unavailable. Try again shortly.",
            )
        return DevOpsApiError(safe_message)

    @staticmethod
    def _require_non_empty(value: str | None, label: str) -> str:
        if value is None or not value.strip():
            msg = f"Azure DevOps {label} is not configured."
            raise DevOpsNotConfiguredError(msg)
        return value.strip()


def _parse_pipeline_name(payload: dict[str, Any], pipeline_id: int) -> str:
    name = payload.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return f"pipeline-{pipeline_id}"


def _parse_runs(
    payload: dict[str, Any],
    *,
    pipeline_id: int,
    pipeline_name: str,
) -> list[DevOpsPipelineRun]:
    items = payload.get("value")
    if not isinstance(items, list):
        return []

    runs: list[DevOpsPipelineRun] = []
    for item in items:
        run = _parse_run_item(
            item,
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
        )
        if run is not None:
            runs.append(run)
    return runs


def _parse_run_item(
    payload: object,
    *,
    pipeline_id: int,
    pipeline_name: str,
) -> DevOpsPipelineRun | None:
    if not isinstance(payload, dict):
        return None

    run_id = payload.get("id")
    run_name = payload.get("name")
    if not isinstance(run_id, int) or not isinstance(run_name, str):
        return None

    pipeline = payload.get("pipeline")
    resolved_pipeline_id = pipeline_id
    resolved_pipeline_name = pipeline_name
    if isinstance(pipeline, dict):
        nested_id = pipeline.get("id")
        nested_name = pipeline.get("name")
        if isinstance(nested_id, int):
            resolved_pipeline_id = nested_id
        if isinstance(nested_name, str) and nested_name.strip():
            resolved_pipeline_name = nested_name.strip()

    return DevOpsPipelineRun(
        pipeline_id=resolved_pipeline_id,
        pipeline_name=resolved_pipeline_name,
        run_id=run_id,
        run_name=run_name,
        status=_normalize_status(payload.get("state")),
        result=_normalize_result(payload.get("result")),
        start_time=_parse_datetime(payload.get("createdDate")),
        finish_time=_parse_datetime(payload.get("finishedDate")),
        source_branch=_parse_source_branch(payload),
        build_url=_parse_build_url(payload.get("url")),
    )


def _normalize_status(value: object) -> DevOpsRunStatus:
    if not isinstance(value, str):
        return DevOpsRunStatus.UNKNOWN
    normalized = value.strip().lower()
    mapping = {
        "queued": DevOpsRunStatus.QUEUED,
        "inprogress": DevOpsRunStatus.IN_PROGRESS,
        "in_progress": DevOpsRunStatus.IN_PROGRESS,
        "completed": DevOpsRunStatus.COMPLETED,
        "canceling": DevOpsRunStatus.CANCELING,
    }
    return mapping.get(normalized, DevOpsRunStatus.UNKNOWN)


def _normalize_result(value: object) -> DevOpsRunResult:
    if value is None:
        return DevOpsRunResult.NONE
    if not isinstance(value, str):
        return DevOpsRunResult.UNKNOWN
    normalized = value.strip().lower()
    mapping = {
        "succeeded": DevOpsRunResult.SUCCEEDED,
        "failed": DevOpsRunResult.FAILED,
        "canceled": DevOpsRunResult.CANCELED,
        "cancelled": DevOpsRunResult.CANCELED,
        "partiallysucceeded": DevOpsRunResult.PARTIALLY_SUCCEEDED,
        "partially_succeeded": DevOpsRunResult.PARTIALLY_SUCCEEDED,
    }
    return mapping.get(normalized, DevOpsRunResult.UNKNOWN)


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _parse_source_branch(payload: dict[str, Any]) -> str | None:
    resources = payload.get("resources")
    if not isinstance(resources, dict):
        return None
    repositories = resources.get("repositories")
    if not isinstance(repositories, dict):
        return None
    for repository in repositories.values():
        if not isinstance(repository, dict):
            continue
        ref_name = repository.get("refName")
        if isinstance(ref_name, str) and ref_name.strip():
            return _normalize_branch_ref(ref_name.strip())
    return None


def _normalize_branch_ref(ref_name: str) -> str:
    prefix = "refs/heads/"
    if ref_name.startswith(prefix):
        return ref_name[len(prefix) :]
    return ref_name


def _parse_build_url(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
