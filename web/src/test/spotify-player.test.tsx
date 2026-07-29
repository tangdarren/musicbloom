import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../api/client";
import type { SpotifyPlayerSnapshot } from "../api/spotifyPlayerTypes";
import { PlaybackModeProvider } from "../player/PlaybackModeContext";
import { PlayerProvider } from "../player/PlayerContext";
import { PlaybackStudio } from "../components/player/PlaybackStudio";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

const spotifySnapshot: SpotifyPlayerSnapshot = {
  status: "playing",
  configured: true,
  connected: true,
  is_playing: true,
  progress_ms: 30_000,
  track: {
    track_id: "track-123",
    title: "Garden Echoes",
    artist_name: "Petal & Pine",
    album_title: "Greenhouse Echoes",
    duration_ms: 210_000,
    artwork_url: "https://i.scdn.co/image/example.png",
    spotify_uri: "spotify:track:track-123",
  },
  device: {
    id: "device-123",
    name: "Bloom Laptop",
    type: "Computer",
    is_active: true,
    volume_percent: 60,
  },
  shuffle: false,
  repeat_mode: "off",
  recently_played: [],
  message: null,
  control_available: true,
  control_unavailable_reason: null,
};

function renderStudio() {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <PlaybackModeProvider>
        <PlayerProvider>
          <PlaybackStudio />
        </PlayerProvider>
      </PlaybackModeProvider>
    </QueryProvider>,
  );
}

describe("Spotify playback integration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
    vi.spyOn(apiClient, "getSpotifyStatus").mockResolvedValue({
      status: "connected",
      configured: true,
      display_name: "Bloom Listener",
      spotify_user_id: "spotify-user-123",
      scopes: ["user-modify-playback-state"],
      expires_at: null,
      error_code: null,
      error_message: null,
    });
    vi.spyOn(apiClient, "getSpotifyPlayer").mockResolvedValue(spotifySnapshot);
    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue({
      state: "stopped",
      active_track: null,
      queue: [],
      queue_index: null,
      volume: { level: 0.8 },
      shuffle: false,
      repeat_mode: "off",
    });
    vi.spyOn(apiClient, "getTracks").mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    });
  });

  it("keeps demo mode active by default", async () => {
    renderStudio();

    expect(await screen.findByText("Demo mode")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Demo Mode" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("switches to Spotify mode when the user selects it", async () => {
    const user = userEvent.setup();
    renderStudio();

    await screen.findByText("Demo mode");
    await user.click(screen.getByRole("button", { name: "Spotify Mode" }));

    expect(await screen.findByText("Spotify mode")).toBeInTheDocument();
    expect(await screen.findByText("Garden Echoes")).toBeInTheDocument();
  });

  it("shows Spotify control errors from the API", async () => {
    const user = userEvent.setup();
    vi.spyOn(apiClient, "spotifyPause").mockRejectedValue(
      new Error("No active Spotify device found."),
    );

    renderStudio();
    await screen.findByText("Demo mode");
    await user.click(screen.getByRole("button", { name: "Spotify Mode" }));
    await screen.findByText("Garden Echoes");

    await user.click(screen.getByRole("button", { name: "Pause playback" }));

    await waitFor(() => {
      expect(
        screen.getByText("No active Spotify device found."),
      ).toBeInTheDocument();
    });
  });
});
