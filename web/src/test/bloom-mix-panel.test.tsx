import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { apiClient } from "../api/client";
import type { Track } from "../api/types";
import { BloomMixPanel } from "../components/player/BloomMixPanel";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

function renderPanel() {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <BloomMixPanel />
    </QueryProvider>,
  );
}

function makeTrack(
  overrides: Partial<Track> & Pick<Track, "id" | "title" | "mood">,
): Track {
  return {
    artist_id: "artist-petal-pine",
    artist_name: overrides.artist_name ?? "Petal & Pine",
    album_id: "album-greenhouse-echoes",
    album_title: "Greenhouse Echoes",
    duration_ms: overrides.duration_ms ?? 180_000,
    artwork: {
      local_path: `/static/demo/artwork/${overrides.id}.png`,
    },
    audio: { local_path: `/static/demo/audio/${overrides.id}.wav` },
    genre: "acoustic garden",
    accent_theme: {
      primary: "#7BC47F",
      secondary: "#F4E1A1",
      background: "#F7FBF4",
    },
    playable_in_demo_mode: true,
    ...overrides,
  };
}

const calmTracks: Track[] = [
  makeTrack({ id: "calm-a", title: "Morning Dew Waltz", mood: "calm" }),
  makeTrack({
    id: "calm-b",
    title: "Greenhouse Lullaby",
    mood: "calm",
    artist_name: "Leaf Quartet",
  }),
  makeTrack({ id: "calm-c", title: "Pebble Path", mood: "calm" }),
  makeTrack({ id: "calm-d", title: "Moss Notebook", mood: "calm" }),
  makeTrack({ id: "calm-e", title: "Quiet Trellis", mood: "calm" }),
  makeTrack({ id: "calm-f", title: "Fern Window", mood: "calm" }),
];

describe("BloomMixPanel", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows every mood and an initial prompt before selection", () => {
    const getTracksSpy = vi.spyOn(apiClient, "getTracks");

    renderPanel();

    expect(
      screen.getByRole("group", { name: "BloomMix moods" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Calm/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Playful/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Dreamy/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Energetic/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cozy/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Mysterious/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Choose a mood to grow a five-song BloomMix preview/i),
    ).toBeInTheDocument();
    expect(getTracksSpy).not.toHaveBeenCalled();
  });

  it("loads tracks for the selected mood and shows a successful preview", async () => {
    const getTracksSpy = vi.spyOn(apiClient, "getTracks").mockResolvedValue({
      items: calmTracks,
      total: calmTracks.length,
      page: 1,
      page_size: 50,
      total_pages: 1,
    });
    const user = userEvent.setup();

    renderPanel();

    await user.click(screen.getByRole("button", { name: /Calm/i }));

    expect(screen.getByRole("button", { name: /Calm/i })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await waitFor(() => {
      expect(getTracksSpy).toHaveBeenCalledWith({
        mood: "calm",
        page: 1,
        page_size: 50,
      });
    });

    const preview = await screen.findByRole("list");
    const items = within(preview).getAllByRole("listitem");
    expect(items).toHaveLength(5);
    expect(within(items[0]!).getByText(/Petal & Pine|Leaf Quartet/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Refresh mix" })).toBeInTheDocument();
  });

  it("shows a loading state while tracks are fetching", async () => {
    let resolveTracks: ((value: {
      items: Track[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }) => void) | undefined;

    vi.spyOn(apiClient, "getTracks").mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTracks = resolve;
        }),
    );
    const user = userEvent.setup();

    renderPanel();
    await user.click(screen.getByRole("button", { name: /Dreamy/i }));

    expect(
      await screen.findByText("Growing your BloomMix"),
    ).toBeInTheDocument();

    resolveTracks?.({
      items: [
        makeTrack({ id: "dreamy-a", title: "Cloud Terrace", mood: "dreamy" }),
      ],
      total: 1,
      page: 1,
      page_size: 50,
      total_pages: 1,
    });

    expect(await screen.findByText("Cloud Terrace")).toBeInTheDocument();
  });

  it("refreshes the mix ordering without another API request", async () => {
    const getTracksSpy = vi.spyOn(apiClient, "getTracks").mockResolvedValue({
      items: calmTracks,
      total: calmTracks.length,
      page: 1,
      page_size: 50,
      total_pages: 1,
    });
    const user = userEvent.setup();

    renderPanel();
    await user.click(screen.getByRole("button", { name: /Calm/i }));

    const preview = await screen.findByRole("list");
    const firstOrder = within(preview)
      .getAllByRole("listitem")
      .map((item) => item.textContent);

    await user.click(screen.getByRole("button", { name: "Refresh mix" }));

    await waitFor(() => {
      const nextOrder = within(screen.getByRole("list"))
        .getAllByRole("listitem")
        .map((item) => item.textContent);
      expect(nextOrder).not.toEqual(firstOrder);
    });

    expect(getTracksSpy).toHaveBeenCalledTimes(1);
  });

  it("shows an empty state when no playable tracks match", async () => {
    vi.spyOn(apiClient, "getTracks").mockResolvedValue({
      items: [
        makeTrack({
          id: "calm-preview",
          title: "Ghostlight",
          mood: "calm",
          playable_in_demo_mode: false,
          audio: { url: "https://example.com/preview.ogg" },
        }),
        makeTrack({
          id: "calm-missing",
          title: "Broken Path",
          mood: "calm",
          audio: { url: "https://demo.musicbloom.local/audio/missing.ogg" },
        }),
      ],
      total: 2,
      page: 1,
      page_size: 50,
      total_pages: 1,
    });
    const user = userEvent.setup();

    renderPanel();
    await user.click(screen.getByRole("button", { name: /Calm/i }));

    expect(
      await screen.findByText(
        /No playable tracks are available for this mood right now/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Refresh mix" }),
    ).not.toBeInTheDocument();
  });

  it("surfaces API failures for the selected mood", async () => {
    vi.spyOn(apiClient, "getTracks").mockRejectedValue(
      new Error("BloomMix catalog unavailable"),
    );
    const user = userEvent.setup();

    renderPanel();
    await user.click(screen.getByRole("button", { name: /Mysterious/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /BloomMix catalog unavailable/i,
    );
  });
});
