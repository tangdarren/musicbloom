export type DevOpsRunStatus =
  | "queued"
  | "in_progress"
  | "completed"
  | "canceling"
  | "unknown";

export type DevOpsRunResult =
  | "succeeded"
  | "failed"
  | "canceled"
  | "partially_succeeded"
  | "none"
  | "unknown";

export interface DevOpsPipelineRun {
  pipeline_id: number;
  pipeline_name: string;
  run_id: number;
  run_name: string;
  status: DevOpsRunStatus;
  result: DevOpsRunResult;
  start_time: string | null;
  finish_time: string | null;
  source_branch: string | null;
  build_url: string | null;
}

export interface DevOpsStatusSnapshot {
  configured: boolean;
  demo_mode: boolean;
  pipeline_id: number | null;
  pipeline_name: string | null;
  latest_run: DevOpsPipelineRun | null;
  message: string | null;
}

export interface DevOpsRunsSnapshot {
  configured: boolean;
  demo_mode: boolean;
  pipeline_id: number | null;
  pipeline_name: string | null;
  runs: DevOpsPipelineRun[];
  message: string | null;
}
