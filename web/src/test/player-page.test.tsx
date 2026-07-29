import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { apiClient } from "../api/client";
import type { PlayerSession, Track } from "../api/types";
import { PlayerProvider } from "../player/PlayerContext";
import { VisualPlayer } from "../components/player/VisualPlayer";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

function renderPlayer() {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <PlayerProvider>
        <VisualPlayer />
      </PlayerProvider>
    </QueryProvider>,
  );
}

const demoTrack: Track = {
  id: "demo-track-001",
  title: "Morning Dew Waltz",
  artist_id: "artist-petal-pine",
  artist_name: "Petal & Pine",
  album_id: "album-greenhouse-echoes",
  album_title: "Greenhouse Echoes",
  duration_ms: 184_000,
  artwork: { local_path: "/static/demo/artwork/morning-dew-waltz.png" },
  audio: { local_path: "/static/demo/audio/morning-dew-waltz.wav" },
  mood: "calm",
  genre: "acoustic garden",
  accent_theme: {
    primary: "#7BC47F",
    secondary: "#F4E1A1",
    background: "#F7FBF4",
  },
  playable_in_demo_mode: true,
};

const unavailableTrack: Track = {
  ...demoTrack,
  id: "demo-track-002",
  title: "Sunbeam Carousel",
  audio: { url: "https://demo.musicbloom.local/audio/sunbeam-carousel.ogg" },
};

function buildSession(activeTrack: PlayerSession["active_track"] = null): PlayerSession {
  return {
    state: activeTrack ? "playing" : "stopped",
    active_track: activeTrack,
    queue: [],
    queue_index: null,
    volume: { level: 0.8 },
    shuffle: false,
    repeat_mode: "off",
  };
}

function buildActiveTrack() {
  return {
    track_id: demoTrack.id,
    title: demoTrack.title,
    artist_name: demoTrack.artist_name,
    album_title: demoTrack.album_title,
    duration_ms: demoTrack.duration_ms,
    artwork: demoTrack.artwork,
    audio: demoTrack.audio,
    mood: demoTrack.mood,
    genre: demoTrack.genre,
    accent_theme: demoTrack.accent_theme,
    playable_in_demo_mode: true,
    position: { position_ms: 0 },
  };
}

describe("VisualPlayer", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue(buildSession());
    vi.spyOn(apiClient, "getTracks").mockResolvedValue({
      items: [demoTrack, unavailableTrack],
      total: 2,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });
    vi.spyOn(apiClient, "submitListeningEvent").mockResolvedValue({
      id: 1,
      idempotency_key: "demo",
      track_id: demoTrack.id,
      event_type: "started",
      position_ms: 0,
      occurred_at: new Date().toISOString(),
      awards: [],
      melody_points_earned: 0,
      experience_earned: 0,
      duplicate: false,
    });
  });

  it("renders the demo catalog and queues a track", async () => {
    const queueSpy = vi.spyOn(apiClient, "queueTrack").mockResolvedValue(
      buildSession(),
    );
    const user = userEvent.setup();

    renderPlayer();

    expect(await screen.findByText("Morning Dew Waltz")).toBeInTheDocument();
    expect(screen.getByText("Sunbeam Carousel")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Queue Morning Dew Waltz" }));

    await waitFor(() => {
      expect(queueSpy).toHaveBeenCalledWith("demo-track-001");
    });
  });

  it("starts playback through the API when play is clicked", async () => {
    const playSpy = vi.spyOn(apiClient, "play").mockResolvedValue(
      buildSession(buildActiveTrack()),
    );
    const user = userEvent.setup();

    renderPlayer();

    await user.click(
      await screen.findByRole("button", { name: "Play Morning Dew Waltz" }),
    );

    await waitFor(() => {
      expect(playSpy).toHaveBeenCalledWith("demo-track-001");
    });
  });

  it("shows unavailable audio messaging for fictional demo URLs", async () => {
    vi.spyOn(apiClient, "play").mockResolvedValue(
      buildSession({
        ...buildActiveTrack(),
        track_id: unavailableTrack.id,
        title: unavailableTrack.title,
        audio: unavailableTrack.audio,
      }),
    );

    const user = userEvent.setup();

    renderPlayer();

    await user.click(
      await screen.findByRole("button", { name: "Play Sunbeam Carousel" }),
    );

    expect(
      await screen.findByText(/Demo audio is unavailable for this track/i),
    ).toBeInTheDocument();
  });

  it("surfaces API failures", async () => {
    vi.spyOn(apiClient, "getPlayerSession").mockRejectedValue(
      new Error("Player API unavailable"),
    );

    renderPlayer();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Player API unavailable/i,
    );
  });
});
