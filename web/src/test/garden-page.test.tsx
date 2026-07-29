import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { apiClient } from "../api/client";
import type {
  DecorationCatalogEntry,
  GardenState,
} from "../api/gardenTypes";
import { InteractiveGarden } from "../components/garden/InteractiveGarden";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

const baseGarden: GardenState = {
  profile: { garden_name: "Starter Garden", theme: "meadow" },
  mood: "serene",
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
  milestone_plants: [
    {
      id: "milestone-first-track",
      title: "First Sprout",
      description: "Complete your first track",
      target: 1,
      progress: 0,
      unlocked: false,
    },
  ],
  unlocked_decorations: [],
  equipped_decorations: [],
  recent_achievements: [],
  tracks_completed: 0,
  total_listening_minutes: 0,
};

const decorations: DecorationCatalogEntry[] = [
  {
    decoration: {
      id: "decoration-sprout-003",
      name: "First Sprout",
      description: "A tiny sprout",
      slot: "south",
    },
    unlocked: false,
    equipped: false,
  },
];

function renderGarden() {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <InteractiveGarden />
    </QueryProvider>,
  );
}

describe("InteractiveGarden", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(apiClient, "getGarden").mockResolvedValue(baseGarden);
    vi.spyOn(apiClient, "getDecorations").mockResolvedValue(decorations);
    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue({
      state: "stopped",
      active_track: null,
      queue: [],
      queue_index: null,
      volume: { level: 0.8 },
      shuffle: false,
      repeat_mode: "off",
    });
  });

  it("renders empty garden state for new users", async () => {
    renderGarden();

    expect(
      await screen.findByRole("heading", { name: "Your MusicBloom garden" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Starter Garden")).toBeInTheDocument();
    expect(
      screen.getByText(/Complete tracks to grow artist flowers here/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Start listening to unlock your first achievement/i),
    ).toBeInTheDocument();
  });

  it("shows locked decoration state", async () => {
    renderGarden();

    expect(await screen.findByLabelText("Locked")).toBeInTheDocument();
    expect(screen.getByText(/Slot: south · Locked/i)).toBeInTheDocument();
  });

  it("equips an unlocked decoration", async () => {
    const user = userEvent.setup();
    vi.spyOn(apiClient, "getDecorations").mockResolvedValue([
      {
        ...decorations[0],
        unlocked: true,
      },
    ]);
    vi.spyOn(apiClient, "equipDecoration").mockResolvedValue({
      decoration: decorations[0].decoration,
      slot: "south",
      equipped_at: "2026-01-01T00:00:00Z",
    });

    renderGarden();

    const equipButton = await screen.findByRole("button", { name: "Equip" });
    await user.click(equipButton);

    await waitFor(() => {
      expect(apiClient.equipDecoration).toHaveBeenCalledWith(
        "decoration-sprout-003",
      );
    });
  });

  it("renders artist flowers when progress exists", async () => {
    vi.spyOn(apiClient, "getGarden").mockResolvedValue({
      ...baseGarden,
      mood: "cheerful",
      tracks_completed: 1,
      artist_flowers: [
        {
          artist_id: "artist-petal-pine",
          artist_name: "Petal & Pine",
          completions: 1,
          bloom_stage: 1,
        },
      ],
    });

    renderGarden();

    expect(await screen.findByText("Petal & Pine")).toBeInTheDocument();
    expect(screen.getByText("Cheerful")).toBeInTheDocument();
  });
});
