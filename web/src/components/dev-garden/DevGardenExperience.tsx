import { LoadingState } from "../LoadingState";
import { DevGardenRunHistory } from "./DevGardenRunHistory";
import { DevGardenScene } from "./DevGardenScene";
import { DevGardenStatusPanel } from "./DevGardenStatusPanel";
import { formatRefreshTime } from "./devGardenFormat";
import {
  calculateSuccessRate,
  presentDevGardenStatus,
} from "./devGardenState";
import { useDevGarden } from "./useDevGarden";
import { useReducedMotion } from "./useReducedMotion";

export function DevGardenExperience() {
  const reducedMotion = useReducedMotion();
  const {
    status,
    runs,
    isLoading,
    isFetching,
    isError,
    errorMessage,
    isStale,
    lastUpdatedAt,
    refresh,
  } = useDevGarden();

  if (isLoading) {
    return <LoadingState label="Loading Dev Garden pipeline status" />;
  }

  if (isError) {
    return (
      <div className="dev-garden-alert dev-garden-alert--error" role="alert">
        <h2>Could not load pipeline status</h2>
        <p>{errorMessage}</p>
        <button type="button" className="button button--secondary" onClick={() => void refresh()}>
          Try again
        </button>
      </div>
    );
  }

  const latestRun = status?.latest_run ?? null;
  const presentation = presentDevGardenStatus(latestRun);
  const successRate = calculateSuccessRate(runs?.runs ?? []);
  const pipelineName =
    status?.pipeline_name ?? runs?.pipeline_name ?? latestRun?.pipeline_name ?? null;

  return (
    <div className="dev-garden-page__layout">
      <div className="dev-garden-toolbar">
        <p className="dev-garden-toolbar__refresh" role="status" aria-live="polite">
          Last refresh:{" "}
          {lastUpdatedAt > 0 ? formatRefreshTime(lastUpdatedAt) : "—"}
          {isFetching ? " · Updating…" : ""}
        </p>
        <button
          type="button"
          className="button button--secondary"
          onClick={() => void refresh()}
          disabled={isFetching}
        >
          Refresh now
        </button>
      </div>

      {isStale ? (
        <div className="dev-garden-alert dev-garden-alert--stale" role="status">
          Pipeline data may be stale. Refresh to fetch the latest Azure DevOps
          status.
        </div>
      ) : null}

      {!latestRun && !status?.demo_mode ? (
        <div className="dev-garden-alert dev-garden-alert--empty" role="status">
          No recent pipeline runs were returned. BloomBud is resting until the
          next build starts.
        </div>
      ) : null}

      <div className="dev-garden-page__main">
        <div className="dev-garden-page__scene-wrap">
          <DevGardenScene
            visualState={presentation.visualState}
            reducedMotion={reducedMotion}
            sceneDescription={presentation.sceneDescription}
          />
          <p className="dev-garden-scene__caption">{presentation.sceneDescription}</p>
        </div>

        <DevGardenStatusPanel
          pipelineName={pipelineName}
          run={latestRun}
          presentation={presentation}
          successRateLabel={successRate.label}
          demoMode={status?.demo_mode ?? false}
          configured={status?.configured ?? false}
          message={status?.message ?? runs?.message ?? null}
        />
      </div>

      <DevGardenRunHistory runs={runs?.runs ?? []} />
    </div>
  );
}
