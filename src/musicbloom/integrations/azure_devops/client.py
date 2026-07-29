"""Azure DevOps REST API HTTP client."""

import asyncio
import base64
from typing import Any, ClassVar, Protocol

import httpx

from musicbloom.security.secret_redaction import redact_secrets


class AzureDevOpsClient(Protocol):
    """Protocol for Azure DevOps pipeline API interactions."""

    async def get_pipeline(
        self,
        *,
        organization: str,
        project: str,
        pipeline_id: int,
        api_version: str,
        personal_access_token: str,
    ) -> dict[str, Any]:
        """Return pipeline metadata."""

    async def list_pipeline_runs(
        self,
        *,
        organization: str,
        project: str,
        pipeline_id: int,
        api_version: str,
        personal_access_token: str,
        limit: int,
    ) -> dict[str, Any]:
        """Return recent pipeline runs."""


class HttpAzureDevOpsClient:
    """HTTP-backed Azure DevOps pipeline client."""

    _RETRYABLE_STATUS_CODES: ClassVar[set[int]] = {429, 500, 502, 503, 504}
    _MAX_RETRIES = 2
    _RETRY_BACKOFF_SECONDS = 0.25

    def __init__(
        self,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._transport = transport
        self._timeout = timeout_seconds

    async def get_pipeline(
        self,
        *,
        organization: str,
        project: str,
        pipeline_id: int,
        api_version: str,
        personal_access_token: str,
    ) -> dict[str, Any]:
        return await self._request_json(
            method="GET",
            url=_pipeline_url(organization, project, pipeline_id),
            api_version=api_version,
            personal_access_token=personal_access_token,
        )

    async def list_pipeline_runs(
        self,
        *,
        organization: str,
        project: str,
        pipeline_id: int,
        api_version: str,
        personal_access_token: str,
        limit: int,
    ) -> dict[str, Any]:
        return await self._request_json(
            method="GET",
            url=_pipeline_runs_url(organization, project, pipeline_id),
            api_version=api_version,
            personal_access_token=personal_access_token,
            params={"$top": limit},
        )

    async def _request_json(
        self,
        *,
        method: str,
        url: str,
        api_version: str,
        personal_access_token: str,
        params: dict[str, int | str] | None = None,
    ) -> dict[str, Any]:
        query: dict[str, str | int] = {"api-version": api_version}
        if params:
            query.update(params)

        for attempt in range(self._MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    transport=self._transport,
                    timeout=self._timeout,
                ) as client:
                    response = await client.request(
                        method,
                        url,
                        params=query,
                        headers=_auth_headers(personal_access_token),
                    )
            except httpx.HTTPError:
                if attempt >= self._MAX_RETRIES:
                    raise
                await asyncio.sleep(self._RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue

            if response.status_code in self._RETRYABLE_STATUS_CODES:
                if attempt >= self._MAX_RETRIES:
                    response.raise_for_status()
                retry_after = response.headers.get("Retry-After")
                delay = self._RETRY_BACKOFF_SECONDS * (attempt + 1)
                if retry_after and retry_after.isdigit():
                    delay = max(delay, float(retry_after))
                await asyncio.sleep(delay)
                continue

            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                msg = "Azure DevOps response was not an object"
                raise TypeError(msg)
            return payload

        msg = "Azure DevOps request failed"
        raise RuntimeError(msg)


def _pipeline_url(organization: str, project: str, pipeline_id: int) -> str:
    return (
        f"https://dev.azure.com/{organization}/{project}/_apis/pipelines/{pipeline_id}"
    )


def _pipeline_runs_url(organization: str, project: str, pipeline_id: int) -> str:
    return (
        f"https://dev.azure.com/{organization}/{project}/"
        f"_apis/pipelines/{pipeline_id}/runs"
    )


def _auth_headers(personal_access_token: str) -> dict[str, str]:
    token_bytes = f":{personal_access_token}".encode()
    encoded = base64.b64encode(token_bytes).decode("ascii")
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
    }


def sanitize_azure_devops_error_message(
    message: str,
    *,
    personal_access_token: str | None,
) -> str:
    """Remove PAT material from an error message."""
    secrets = [personal_access_token] if personal_access_token else []
    return redact_secrets(message, secrets)
