import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../api/client";
import { TopNav } from "../components/TopNav";
import { QueryProvider } from "../providers/QueryProvider";
import { createAppRouter } from "../routes/router";
import { createTestQueryClient } from "./test-utils";

const gardenState = {
  profile: { garden_name: "Starter Garden", theme: "meadow" },
  mood: "serene" as const,
  level: {
    level: 1,
    experience: {
      total_experience: 0,
      experience_in_level: 0,
      experience_to_next_level: 100,
    },
  },
  melody_points: 0,
  streak: {
    current_days: 0,
    last_listening_utc_date: null,
    bonus_points_awarded_today: 0,
    daily_bonus_cap: 25,
  },
  artist_flowers: [],
  milestone_plants: [],
  unlocked_decorations: [],
  equipped_decorations: [],
  recent_achievements: [],
  tracks_completed: 0,
  total_listening_minutes: 0,
};

const playerSession = {
  state: "stopped" as const,
  active_track: null,
  queue: [],
  queue_index: null,
  volume: { level: 0.8 },
  shuffle: false,
  repeat_mode: "off" as const,
};

function renderWithProviders(ui: React.ReactElement, route = "/") {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryProvider>,
  );
}

describe("routing", () => {
  beforeEach(() => {
    vi.spyOn(apiClient, "getGarden").mockResolvedValue(gardenState);
    vi.spyOn(apiClient, "getDecorations").mockResolvedValue([]);
    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue(playerSession);
    vi.spyOn(apiClient, "getSpotifyStatus").mockResolvedValue({
      status: "disconnected",
      configured: false,
      display_name: null,
      spotify_user_id: null,
      scopes: [],
      expires_at: null,
      error_code: null,
      error_message: null,
    });
    vi.spyOn(apiClient, "getTracks").mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    });
    vi.spyOn(apiClient, "getRecentBlooms").mockResolvedValue({ items: [] });
    vi.spyOn(apiClient, "getDevOpsStatus").mockResolvedValue({
      configured: false,
      demo_mode: true,
      pipeline_id: 42,
      pipeline_name: "musicbloom-ci",
      latest_run: {
        pipeline_id: 42,
        pipeline_name: "musicbloom-ci",
        run_id: 1284,
        run_name: "20260728.42",
        status: "completed",
        result: "succeeded",
        start_time: "2026-07-28T18:00:00Z",
        finish_time: "2026-07-28T18:06:00Z",
        source_branch: "main",
        build_url: "https://dev.azure.com/demo-org/musicbloom/_build/results?buildId=1284",
      },
      message: "Demo pipeline data",
    });
    vi.spyOn(apiClient, "getDevOpsRuns").mockResolvedValue({
      configured: false,
      demo_mode: true,
      pipeline_id: 42,
      pipeline_name: "musicbloom-ci",
      runs: [],
      message: "Demo pipeline data",
    });
  });

  it.each([
    ["/", "Grow your music garden, one song at a time"],
    ["/player", "Garden playback studio"],
    ["/garden", "Your MusicBloom garden"],
    ["/history", "Listening history"],
    ["/quests", "Quest board"],
    ["/achievements", "Achievement gallery"],
    ["/dev-garden", "Dev Garden"],
  ])("renders %s", async (path, heading) => {
    const testRouter = createAppRouter([path]);

    render(
      <QueryProvider client={createTestQueryClient()}>
        <RouterProvider router={testRouter} />
      </QueryProvider>,
    );

    expect(
      await screen.findByRole("heading", { level: 1, name: heading }),
    ).toBeInTheDocument();
  });

  it("shows a not-found page for unknown routes", async () => {
    const testRouter = createAppRouter(["/does-not-exist"]);

    render(
      <QueryProvider client={createTestQueryClient()}>
        <RouterProvider router={testRouter} />
      </QueryProvider>,
    );

    expect(
      await screen.findByRole("heading", { level: 1, name: /Page not found/i }),
    ).toBeInTheDocument();
  });
});

describe("navigation", () => {
  it("renders primary navigation links", () => {
    renderWithProviders(<TopNav />);

    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Player" })).toHaveAttribute(
      "href",
      "/player",
    );
    expect(screen.getByRole("link", { name: "Garden" })).toHaveAttribute(
      "href",
      "/garden",
    );
    expect(screen.getByRole("link", { name: "History" })).toHaveAttribute(
      "href",
      "/history",
    );
    expect(screen.getByRole("link", { name: "Quests" })).toHaveAttribute(
      "href",
      "/quests",
    );
    expect(
      screen.getByRole("link", { name: "Achievements" }),
    ).toHaveAttribute("href", "/achievements");
    expect(screen.getByRole("link", { name: "Dev Garden" })).toHaveAttribute(
      "href",
      "/dev-garden",
    );
  });
});

describe("homepage", () => {
  it("links to the visual player", async () => {
    const testRouter = createAppRouter(["/"]);

    render(
      <QueryProvider client={createTestQueryClient()}>
        <RouterProvider router={testRouter} />
      </QueryProvider>,
    );

    expect(
      await screen.findByRole("link", { name: /Open visual player/i }),
    ).toHaveAttribute("href", "/player");
  });
});
