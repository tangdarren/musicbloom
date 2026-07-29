"""Demo Azure DevOps pipeline status provider."""

from datetime import UTC, datetime, timedelta

from musicbloom.models.devops import (
    DevOpsPipelineRun,
    DevOpsRunResult,
    DevOpsRunsSnapshot,
    DevOpsRunStatus,
    DevOpsStatusSnapshot,
)

DEMO_PIPELINE_ID = 42
DEMO_PIPELINE_NAME = "musicbloom-ci"


class DemoDevOpsPipelineProvider:
    """Return stable demo pipeline data for the Dev Garden."""

    def get_status(self) -> DevOpsStatusSnapshot:
        """Return a healthy demo pipeline status snapshot."""
        runs = self._demo_runs()
        return DevOpsStatusSnapshot(
            configured=False,
            demo_mode=True,
            pipeline_id=DEMO_PIPELINE_ID,
            pipeline_name=DEMO_PIPELINE_NAME,
            latest_run=runs[0],
            message=(
                "Showing demo pipeline status. Configure Azure DevOps credentials "
                "and disable devops demo mode for live build data."
            ),
        )

    def list_runs(self, *, limit: int) -> DevOpsRunsSnapshot:
        """Return recent demo pipeline runs."""
        runs = self._demo_runs()[:limit]
        return DevOpsRunsSnapshot(
            configured=False,
            demo_mode=True,
            pipeline_id=DEMO_PIPELINE_ID,
            pipeline_name=DEMO_PIPELINE_NAME,
            runs=runs,
            message=(
                "Showing demo pipeline runs. Configure Azure DevOps credentials "
                "and disable devops demo mode for live build data."
            ),
        )

    def _demo_runs(self) -> list[DevOpsPipelineRun]:
        now = datetime.now(tz=UTC)
        return [
            DevOpsPipelineRun(
                pipeline_id=DEMO_PIPELINE_ID,
                pipeline_name=DEMO_PIPELINE_NAME,
                run_id=1284,
                run_name="20260728.42",
                status=DevOpsRunStatus.COMPLETED,
                result=DevOpsRunResult.SUCCEEDED,
                start_time=now - timedelta(minutes=18),
                finish_time=now - timedelta(minutes=12),
                source_branch="main",
                build_url=(
                    "https://dev.azure.com/demo-org/musicbloom/_build/results?buildId=1284"
                ),
            ),
            DevOpsPipelineRun(
                pipeline_id=DEMO_PIPELINE_ID,
                pipeline_name=DEMO_PIPELINE_NAME,
                run_id=1283,
                run_name="20260727.41",
                status=DevOpsRunStatus.COMPLETED,
                result=DevOpsRunResult.SUCCEEDED,
                start_time=now - timedelta(hours=26),
                finish_time=now - timedelta(hours=25, minutes=54),
                source_branch="main",
                build_url=(
                    "https://dev.azure.com/demo-org/musicbloom/_build/results?buildId=1283"
                ),
            ),
            DevOpsPipelineRun(
                pipeline_id=DEMO_PIPELINE_ID,
                pipeline_name=DEMO_PIPELINE_NAME,
                run_id=1282,
                run_name="20260726.40",
                status=DevOpsRunStatus.COMPLETED,
                result=DevOpsRunResult.FAILED,
                start_time=now - timedelta(days=2, hours=3),
                finish_time=now - timedelta(days=2, hours=2, minutes=52),
                source_branch="feature/dev-garden",
                build_url=(
                    "https://dev.azure.com/demo-org/musicbloom/_build/results?buildId=1282"
                ),
            ),
        ]
