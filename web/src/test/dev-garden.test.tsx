import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../api/client";
import type {
  DevOpsPipelineRun,
  DevOpsRunsSnapshot,
  DevOpsStatusSnapshot,
} from "../api/devopsTypes";
import { DevGardenExperience } from "../components/dev-garden/DevGardenExperience";
import { DevGardenScene } from "../components/dev-garden/DevGardenScene";
import { presentDevGardenStatus } from "../components/dev-garden/devGardenState";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

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

function buildStatus(
  run: DevOpsPipelineRun | null,
  overrides: Partial<DevOpsStatusSnapshot> = {},
): DevOpsStatusSnapshot {
  return {
    configured: false,
    demo_mode: true,
    pipeline_id: 42,
    pipeline_name: "musicbloom-ci",
    latest_run: run,
    message: "Demo pipeline data",
    ...overrides,
  };
}

function buildRuns(
  runs: DevOpsPipelineRun[],
  overrides: Partial<DevOpsRunsSnapshot> = {},
): DevOpsRunsSnapshot {
  return {
    configured: false,
    demo_mode: true,
    pipeline_id: 42,
    pipeline_name: "musicbloom-ci",
    runs,
    message: "Demo pipeline data",
    ...overrides,
  };
}

function renderDevGarden() {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <DevGardenExperience />
    </QueryProvider>,
  );
}

describe("DevGardenScene", () => {
  it.each([
    ["succeeded", buildRun({ result: "succeeded", status: "completed" })],
    ["running", buildRun({ result: "none", status: "in_progress" })],
    ["failed", buildRun({ result: "failed", status: "completed" })],
    [
      "partially_succeeded",
      buildRun({ result: "partially_succeeded", status: "completed" }),
    ],
    ["canceled", buildRun({ result: "canceled", status: "completed" })],
    ["empty", null],
  ] as const)("renders the %s visual state", (expected, run) => {
    const presentation = presentDevGardenStatus(run);

    render(
      <DevGardenScene
        visualState={presentation.visualState}
        reducedMotion
        sceneDescription={presentation.sceneDescription}
      />,
    );

    expect(screen.getByTestId("dev-garden-scene")).toHaveAttribute(
      "data-visual-state",
      expected,
    );
    expect(screen.getByRole("img", { hidden: true })).toHaveAttribute(
      "aria-label",
      presentation.sceneDescription,
    );
  });
});

describe("DevGardenExperience", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(window, "matchMedia").mockImplementation(
      (query: string) =>
        ({
          matches: query === "(prefers-reduced-motion: reduce)",
          media: query,
          onchange: null,
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
          addListener: vi.fn(),
          removeListener: vi.fn(),
        }) as MediaQueryList,
    );
  });

  it("shows loading state while pipeline data is fetched", () => {
    vi.spyOn(apiClient, "getDevOpsStatus").mockReturnValue(new Promise(() => undefined));
    vi.spyOn(apiClient, "getDevOpsRuns").mockReturnValue(new Promise(() => undefined));

    renderDevGarden();

    expect(
      screen.getByText(/Loading Dev Garden pipeline status/i),
    ).toBeInTheDocument();
  });

  it("shows an error state when the API fails", async () => {
    vi.spyOn(apiClient, "getDevOpsStatus").mockRejectedValue(
      new Error("Azure DevOps rate limit reached"),
    );
    vi.spyOn(apiClient, "getDevOpsRuns").mockRejectedValue(
      new Error("Azure DevOps rate limit reached"),
    );

    renderDevGarden();

    expect(
      await screen.findByRole("heading", {
        name: /Could not load pipeline status/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/rate limit reached/i)).toBeInTheDocument();
  });

  it("renders demo mode, metadata, and recent runs", async () => {
    vi.spyOn(apiClient, "getDevOpsStatus").mockResolvedValue(
      buildStatus(buildRun()),
    );
    vi.spyOn(apiClient, "getDevOpsRuns").mockResolvedValue(
      buildRuns([
        buildRun(),
        buildRun({ run_id: 101, run_name: "20260727.2", result: "failed" }),
      ]),
    );

    renderDevGarden();

    expect(await screen.findByText("Demo mode")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Pipeline status/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Succeeded").length).toBeGreaterThan(0);
    expect(screen.getAllByText("musicbloom-ci").length).toBeGreaterThan(0);
    expect(screen.getAllByText("main").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /Open in Azure DevOps/i })).toHaveAttribute(
      "target",
      "_blank",
    );
    expect(screen.getByRole("link", { name: /Open in Azure DevOps/i })).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );
    expect(screen.getByRole("columnheader", { name: "Run" })).toBeInTheDocument();
    expect(screen.getByRole("rowheader", { name: "20260727.2" })).toBeInTheDocument();
  });

  it("shows an empty-state message when there is no recent run", async () => {
    vi.spyOn(apiClient, "getDevOpsStatus").mockResolvedValue(
      buildStatus(null, { demo_mode: false, configured: true }),
    );
    vi.spyOn(apiClient, "getDevOpsRuns").mockResolvedValue(buildRuns([]));

    renderDevGarden();

    expect(
      await screen.findByText(/No recent pipeline runs were returned/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("dev-garden-scene")).toHaveAttribute(
      "data-visual-state",
      "empty",
    );
  });

  it("allows manual refresh", async () => {
    const user = userEvent.setup();
    const statusSpy = vi
      .spyOn(apiClient, "getDevOpsStatus")
      .mockResolvedValue(buildStatus(buildRun()));
    const runsSpy = vi
      .spyOn(apiClient, "getDevOpsRuns")
      .mockResolvedValue(buildRuns([buildRun()]));

    renderDevGarden();

    expect(
      await screen.findByRole("heading", { name: /Pipeline status/i }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Refresh now/i }));

    await waitFor(() => {
      expect(statusSpy.mock.calls.length).toBeGreaterThan(1);
      expect(runsSpy.mock.calls.length).toBeGreaterThan(1);
    });
  });
});
