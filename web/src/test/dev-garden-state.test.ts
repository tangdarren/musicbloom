import { describe, expect, it } from "vitest";

import type { DevOpsPipelineRun } from "../api/devopsTypes";
import {
  calculateSuccessRate,
  deriveDevGardenVisualState,
  isDevGardenDataStale,
  presentDevGardenStatus,
} from "../components/dev-garden/devGardenState";

function buildRun(
  overrides: Partial<DevOpsPipelineRun> = {},
): DevOpsPipelineRun {
  return {
    pipeline_id: 42,
    pipeline_name: "musicbloom-ci",
    run_id: 100,
    run_name: "20260728.1",
    status: "completed",
    result: "succeeded",
    start_time: "2026-07-28T18:00:00Z",
    finish_time: "2026-07-28T18:06:00Z",
    source_branch: "main",
    build_url: "https://dev.azure.com/demo-org/musicbloom/_build/results?buildId=100",
    ...overrides,
  };
}

describe("deriveDevGardenVisualState", () => {
  it.each([
    ["succeeded", buildRun({ result: "succeeded", status: "completed" })],
    ["running", buildRun({ result: "none", status: "in_progress" })],
    ["running", buildRun({ result: "none", status: "queued" })],
    ["failed", buildRun({ result: "failed", status: "completed" })],
    [
      "partially_succeeded",
      buildRun({ result: "partially_succeeded", status: "completed" }),
    ],
    ["canceled", buildRun({ result: "canceled", status: "completed" })],
    ["canceled", buildRun({ result: "none", status: "canceling" })],
    ["empty", null],
  ] as const)("maps to %s", (expected, run) => {
    expect(deriveDevGardenVisualState(run)).toBe(expected);
  });
});

describe("presentDevGardenStatus", () => {
  it("includes text labels and icons for each visual state", () => {
    const presentation = presentDevGardenStatus(
      buildRun({ result: "succeeded", status: "completed" }),
    );

    expect(presentation.visualState).toBe("succeeded");
    expect(presentation.icon).toBe("✓");
    expect(presentation.resultLabel).toBe("Succeeded");
    expect(presentation.statusLabel).toBe("Completed");
    expect(presentation.sceneDescription).toContain("waters a healthy plant");
  });
});

describe("calculateSuccessRate", () => {
  it("summarizes recent completed runs", () => {
    const summary = calculateSuccessRate([
      buildRun({ result: "succeeded" }),
      buildRun({ run_id: 101, result: "failed" }),
      buildRun({ run_id: 102, result: "partially_succeeded" }),
    ]);

    expect(summary.rate).toBe(67);
    expect(summary.label).toContain("67%");
  });

  it("handles empty history", () => {
    expect(calculateSuccessRate([]).label).toBe("No completed runs yet");
  });
});

describe("isDevGardenDataStale", () => {
  it("marks data stale after the configured window", () => {
    const lastUpdatedAt = Date.parse("2026-07-28T18:00:00Z");
    const freshNow = Date.parse("2026-07-28T18:00:30Z");
    const staleNow = Date.parse("2026-07-28T18:01:00Z");

    expect(isDevGardenDataStale(lastUpdatedAt, freshNow)).toBe(false);
    expect(isDevGardenDataStale(lastUpdatedAt, staleNow)).toBe(true);
  });
});
