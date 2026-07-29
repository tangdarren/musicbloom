import type { DevOpsPipelineRun } from "../../api/devopsTypes";
import {
  formatDevGardenDuration,
  formatDevGardenTimestamp,
} from "./devGardenFormat";
import type { DevGardenStatusPresentation } from "./devGardenState";

interface DevGardenStatusPanelProps {
  pipelineName: string | null;
  run: DevOpsPipelineRun | null;
  presentation: DevGardenStatusPresentation;
  successRateLabel: string;
  demoMode: boolean;
  configured: boolean;
  message: string | null;
}

export function DevGardenStatusPanel({
  pipelineName,
  run,
  presentation,
  successRateLabel,
  demoMode,
  configured,
  message,
}: DevGardenStatusPanelProps) {
  return (
    <section
      className="dev-garden-status"
      aria-labelledby="dev-garden-status-heading"
    >
      <div className="dev-garden-status__header">
        <h2 id="dev-garden-status-heading">Pipeline status</h2>
        {demoMode ? (
          <span className="dev-garden-badge dev-garden-badge--demo">
            Demo mode
          </span>
        ) : null}
        {!demoMode && configured ? (
          <span className="dev-garden-badge dev-garden-badge--live">
            Live Azure DevOps
          </span>
        ) : null}
      </div>

      <div
        className={`dev-garden-status__banner dev-garden-status__banner--${presentation.visualState}`}
        role="status"
      >
        <span className="dev-garden-status__icon" aria-hidden="true">
          {presentation.icon}
        </span>
        <div>
          <p className="dev-garden-status__primary">
            {presentation.resultLabel}
          </p>
          <p className="dev-garden-status__secondary">
            {presentation.statusLabel}
          </p>
        </div>
      </div>

      <dl className="dev-garden-status__grid">
        <div>
          <dt>Pipeline</dt>
          <dd>{pipelineName ?? "—"}</dd>
        </div>
        <div>
          <dt>Branch</dt>
          <dd>{run?.source_branch ?? "—"}</dd>
        </div>
        <div>
          <dt>Run</dt>
          <dd>{run?.run_name ?? "No recent run"}</dd>
        </div>
        <div>
          <dt>Started</dt>
          <dd>{formatDevGardenTimestamp(run?.start_time ?? null)}</dd>
        </div>
        <div>
          <dt>Finished</dt>
          <dd>{formatDevGardenTimestamp(run?.finish_time ?? null)}</dd>
        </div>
        <div>
          <dt>Duration</dt>
          <dd>
            {formatDevGardenDuration(
              run?.start_time ?? null,
              run?.finish_time ?? null,
            )}
          </dd>
        </div>
        <div>
          <dt>Success rate</dt>
          <dd>{successRateLabel}</dd>
        </div>
        <div>
          <dt>Build link</dt>
          <dd>
            {run?.build_url ? (
              <a
                href={run.build_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open in Azure DevOps
              </a>
            ) : (
              "—"
            )}
          </dd>
        </div>
      </dl>

      {message ? <p className="dev-garden-status__message">{message}</p> : null}
    </section>
  );
}
