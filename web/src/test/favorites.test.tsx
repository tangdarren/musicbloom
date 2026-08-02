import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../api/client";
import type { FavoriteTrackItem, Track } from "../api/types";
import { FavoritesPanel } from "../components/player/FavoritesPanel";
import { TrackBrowser } from "../components/player/TrackBrowser";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

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

const favoriteItem: FavoriteTrackItem = {
  id: 1,
  track_id: demoTrack.id,
  title: demoTrack.title,
  artist_name: demoTrack.artist_name,
  artwork: demoTrack.artwork,
  duration_ms: demoTrack.duration_ms,
  playable_in_demo_mode: true,
  favorited_at: "2026-08-01T18:00:00Z",
};

describe("favorites UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows empty favorites and toggles a track from the browser", async () => {
    vi.spyOn(apiClient, "getFavorites").mockResolvedValue({ items: [] });
    const addSpy = vi
      .spyOn(apiClient, "addFavorite")
      .mockResolvedValue(favoriteItem);
    vi.spyOn(apiClient, "removeFavorite").mockResolvedValue(undefined);

    const user = userEvent.setup();
    const onToggleFavorite = vi.fn((trackId: string) => {
      void apiClient.addFavorite(trackId);
    });

    render(
      <QueryProvider client={createTestQueryClient()}>
        <FavoritesPanel
          favorites={[]}
          isLoading={false}
          isError={false}
          isToggling={() => false}
          onToggleFavorite={onToggleFavorite}
          onPlay={vi.fn()}
          onQueue={vi.fn()}
        />
        <TrackBrowser
          tracks={[demoTrack]}
          activeTrackId={null}
          favoritedTrackIds={new Set()}
          onPlay={vi.fn()}
          onQueue={vi.fn()}
          onToggleFavorite={onToggleFavorite}
        />
      </QueryProvider>,
    );

    expect(
      screen.getByText(/No favorites yet/i),
    ).toBeInTheDocument();

    const favoriteButton = screen.getByRole("button", {
      name: "Add Morning Dew Waltz to favorites",
    });
    expect(favoriteButton).toHaveAttribute("aria-pressed", "false");

    await user.click(favoriteButton);

    expect(onToggleFavorite).toHaveBeenCalledWith("demo-track-001");
    await waitFor(() => {
      expect(addSpy).toHaveBeenCalledWith("demo-track-001");
    });
  });

  it("shows favorited state and supports play from the favorites panel", async () => {
    const onPlay = vi.fn();
    const onToggleFavorite = vi.fn();
    const user = userEvent.setup();

    render(
      <FavoritesPanel
        favorites={[favoriteItem]}
        isLoading={false}
        isError={false}
        isToggling={() => false}
        onToggleFavorite={onToggleFavorite}
        onPlay={onPlay}
        onQueue={vi.fn()}
      />,
    );

    const removeButton = screen.getByRole("button", {
      name: "Remove Morning Dew Waltz from favorites",
    });
    expect(removeButton).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "Play Morning Dew Waltz" }));
    expect(onPlay).toHaveBeenCalledWith("demo-track-001");

    await user.click(removeButton);
    expect(onToggleFavorite).toHaveBeenCalledWith("demo-track-001");
  });

  it("shows favorited pressed state in the track browser", () => {
    render(
      <TrackBrowser
        tracks={[demoTrack]}
        activeTrackId={null}
        favoritedTrackIds={new Set(["demo-track-001"])}
        onPlay={vi.fn()}
        onQueue={vi.fn()}
        onToggleFavorite={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "Remove Morning Dew Waltz from favorites",
      }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});
