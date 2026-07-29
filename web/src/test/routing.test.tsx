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
  });

  it.each([
    ["/", "Grow your music garden, one song at a time"],
    ["/player", "Garden playback studio"],
    ["/garden", "Your MusicBloom garden"],
    ["/quests", "Quest board"],
    ["/achievements", "Achievement gallery"],
    ["/dev-garden", "Dev garden sandbox"],
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
