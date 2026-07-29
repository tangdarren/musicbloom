import type { DevOpsPipelineRun } from "../../api/devopsTypes";
import {
  formatDevGardenDuration,
  formatDevGardenTimestamp,
} from "./devGardenFormat";
import {
  formatDevOpsResultLabel,
  formatDevOpsStatusLabel,
} from "./devGardenState";

interface DevGardenRunHistoryProps {
  runs: DevOpsPipelineRun[];
}

export function DevGardenRunHistory({ runs }: DevGardenRunHistoryProps) {
  if (runs.length === 0) {
    return (
      <section className="dev-garden-history" aria-labelledby="dev-garden-history-heading">
        <h2 id="dev-garden-history-heading">Recent runs</h2>
        <p className="dev-garden-history__empty" role="status">
          No recent pipeline runs to display yet.
        </p>
      </section>
    );
  }

  return (
    <section className="dev-garden-history" aria-labelledby="dev-garden-history-heading">
      <h2 id="dev-garden-history-heading">Recent runs</h2>
      <div className="dev-garden-history__table-wrap">
        <table className="dev-garden-history__table">
          <caption className="visually-hidden">
            Recent Azure DevOps pipeline runs ordered from newest to oldest
          </caption>
          <thead>
            <tr>
              <th scope="col">Run</th>
              <th scope="col">Result</th>
              <th scope="col">State</th>
              <th scope="col">Branch</th>
              <th scope="col">Duration</th>
              <th scope="col">Finished</th>
              <th scope="col">Build</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id}>
                <th scope="row">{run.run_name}</th>
                <td>{formatDevOpsResultLabel(run.result)}</td>
                <td>{formatDevOpsStatusLabel(run.status)}</td>
                <td>{run.source_branch ?? "—"}</td>
                <td>
                  {formatDevGardenDuration(run.start_time, run.finish_time)}
                </td>
                <td>{formatDevGardenTimestamp(run.finish_time)}</td>
                <td>
                  {run.build_url ? (
                    <a
                      href={run.build_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View build
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ol className="dev-garden-history__timeline" aria-label="Recent run timeline">
        {runs.map((run) => (
          <li key={`timeline-${run.run_id}`}>
            <span className="dev-garden-history__timeline-dot" aria-hidden="true" />
            <div>
              <strong>{run.run_name}</strong>
              <span>
                {" "}
                — {formatDevOpsResultLabel(run.result)} ·{" "}
                {formatDevOpsStatusLabel(run.status)}
              </span>
              <p className="dev-garden-history__timeline-meta">
                {formatDevGardenTimestamp(run.finish_time ?? run.start_time)}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
