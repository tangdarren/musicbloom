"""Domain models for Azure DevOps pipeline status."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DevOpsRunStatus(StrEnum):
    """Normalized Azure DevOps pipeline run status."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELING = "canceling"
    UNKNOWN = "unknown"


class DevOpsRunResult(StrEnum):
    """Normalized Azure DevOps pipeline run result."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    NONE = "none"
    UNKNOWN = "unknown"


class DevOpsPipelineRun(BaseModel):
    """Normalized Azure DevOps pipeline run without secret material."""

    pipeline_id: int = Field(description="Azure DevOps pipeline identifier")
    pipeline_name: str = Field(description="Azure DevOps pipeline display name")
    run_id: int = Field(description="Azure DevOps pipeline run identifier")
    run_name: str = Field(description="Azure DevOps pipeline run display name")
    status: DevOpsRunStatus = Field(description="Normalized run status")
    result: DevOpsRunResult = Field(description="Normalized run result")
    start_time: datetime | None = Field(
        default=None,
        description="UTC timestamp when the run started",
    )
    finish_time: datetime | None = Field(
        default=None,
        description="UTC timestamp when the run finished",
    )
    source_branch: str | None = Field(
        default=None,
        description="Source branch name when available",
    )
    build_url: str | None = Field(
        default=None,
        description="Public Azure DevOps build results URL",
    )


class DevOpsStatusSnapshot(BaseModel):
    """Current Dev Garden pipeline health snapshot."""

    configured: bool = Field(
        description="Whether Azure DevOps credentials are configured on the server",
    )
    demo_mode: bool = Field(
        description="Whether demo pipeline data is being served",
    )
    pipeline_id: int | None = Field(
        default=None,
        description="Configured pipeline identifier",
    )
    pipeline_name: str | None = Field(
        default=None,
        description="Configured pipeline display name",
    )
    latest_run: DevOpsPipelineRun | None = Field(
        default=None,
        description="Most recent pipeline run when available",
    )
    message: str | None = Field(
        default=None,
        description="Informational message for demo or unavailable states",
    )


class DevOpsRunsSnapshot(BaseModel):
    """Recent Azure DevOps pipeline runs for the Dev Garden."""

    configured: bool = Field(
        description="Whether Azure DevOps credentials are configured on the server",
    )
    demo_mode: bool = Field(
        description="Whether demo pipeline data is being served",
    )
    pipeline_id: int | None = Field(
        default=None,
        description="Configured pipeline identifier",
    )
    pipeline_name: str | None = Field(
        default=None,
        description="Configured pipeline display name",
    )
    runs: list[DevOpsPipelineRun] = Field(
        default_factory=list,
        description="Recent pipeline runs ordered from newest to oldest",
    )
    message: str | None = Field(
        default=None,
        description="Informational message for demo or unavailable states",
    )
