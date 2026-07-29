import type {
  DevOpsPipelineRun,
  DevOpsRunResult,
  DevOpsRunStatus,
} from "../../api/devopsTypes";

export type DevGardenVisualState =
  | "succeeded"
  | "running"
  | "failed"
  | "partially_succeeded"
  | "canceled"
  | "empty";

export interface DevGardenStatusPresentation {
  visualState: DevGardenVisualState;
  statusLabel: string;
  resultLabel: string;
  icon: string;
  sceneDescription: string;
}

const RUNNING_STATUSES: DevOpsRunStatus[] = [
  "queued",
  "in_progress",
  "canceling",
];

export function deriveDevGardenVisualState(
  run: DevOpsPipelineRun | null | undefined,
): DevGardenVisualState {
  if (!run) {
    return "empty";
  }

  if (run.result === "canceled" || run.status === "canceling") {
    return "canceled";
  }

  if (run.result === "partially_succeeded") {
    return "partially_succeeded";
  }

  if (run.result === "failed") {
    return "failed";
  }

  if (run.result === "succeeded") {
    return "succeeded";
  }

  if (RUNNING_STATUSES.includes(run.status) || run.result === "none") {
    return "running";
  }

  return "empty";
}

export function formatDevOpsStatusLabel(status: DevOpsRunStatus): string {
  switch (status) {
    case "queued":
      return "Queued";
    case "in_progress":
      return "In progress";
    case "completed":
      return "Completed";
    case "canceling":
      return "Canceling";
    default:
      return "Unknown";
  }
}

export function formatDevOpsResultLabel(result: DevOpsRunResult): string {
  switch (result) {
    case "succeeded":
      return "Succeeded";
    case "failed":
      return "Failed";
    case "canceled":
      return "Canceled";
    case "partially_succeeded":
      return "Partially succeeded";
    case "none":
      return "No result yet";
    default:
      return "Unknown";
  }
}

export function describeDevGardenScene(visualState: DevGardenVisualState): string {
  switch (visualState) {
    case "succeeded":
      return "BloomBud waters a healthy plant after a successful pipeline run.";
    case "running":
      return "BloomBud works at a tiny laptop while the pipeline is running.";
    case "failed":
      return "A plant wilts beside an error sign after a failed pipeline run.";
    case "partially_succeeded":
      return "Clouds drift over the garden after a partially successful run.";
    case "canceled":
      return "BloomBud puts away the watering can after a canceled run.";
    default:
      return "BloomBud sleeps beside an empty flower pot with no recent runs.";
  }
}

export function presentDevGardenStatus(
  run: DevOpsPipelineRun | null | undefined,
): DevGardenStatusPresentation {
  const visualState = deriveDevGardenVisualState(run);

  const statusLabel = run
    ? formatDevOpsStatusLabel(run.status)
    : "No recent run";
  const resultLabel = run
    ? formatDevOpsResultLabel(run.result)
    : "Waiting for data";

  const icon = {
    succeeded: "✓",
    running: "⟳",
    failed: "✕",
    partially_succeeded: "◐",
    canceled: "⊘",
    empty: "💤",
  }[visualState];

  return {
    visualState,
    statusLabel,
    resultLabel,
    icon,
    sceneDescription: describeDevGardenScene(visualState),
  };
}

export function isDevGardenDataStale(
  lastUpdatedAt: number,
  now: number,
  staleAfterMs = 45_000,
): boolean {
  return lastUpdatedAt > 0 && now - lastUpdatedAt > staleAfterMs;
}

export function calculateSuccessRate(
  runs: DevOpsPipelineRun[],
): { rate: number | null; label: string } {
  const completedRuns = runs.filter(
    (run) => run.status === "completed" && run.result !== "none",
  );

  if (completedRuns.length === 0) {
    return { rate: null, label: "No completed runs yet" };
  }

  const successes = completedRuns.filter(
    (run) => run.result === "succeeded" || run.result === "partially_succeeded",
  ).length;

  const rate = Math.round((successes / completedRuns.length) * 100);
  return {
    rate,
    label: `${rate}% success (${successes}/${completedRuns.length} recent runs)`,
  };
}
