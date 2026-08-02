import { describe, expect, it, vi } from "vitest";

import { apiClient, getAudioAvailability, resolveMediaPath } from "../api/client";
import { ApiError, NetworkError } from "../api/types";

describe("api client", () => {
  it("parses health responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () =>
          JSON.stringify({ status: "healthy", service: "musicbloom-api" }),
      }),
    );

    await expect(apiClient.getHealth()).resolves.toEqual({
      status: "healthy",
      service: "musicbloom-api",
    });
  });

  it("raises ApiError for non-success responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        text: async () => "unavailable",
      }),
    );

    await expect(apiClient.getHealth()).rejects.toBeInstanceOf(ApiError);
  });

  it("raises NetworkError when fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed")));

    await expect(apiClient.getHealth()).rejects.toBeInstanceOf(NetworkError);
  });

  it("posts listening events to the progression API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () =>
          JSON.stringify({
            id: 1,
            idempotency_key: "demo-track-001:started",
            track_id: "demo-track-001",
            event_type: "started",
            position_ms: 0,
            occurred_at: "2026-01-01T00:00:00Z",
            awards: [],
            melody_points_earned: 0,
            experience_earned: 0,
            duplicate: false,
          }),
      }),
    );

    await expect(
      apiClient.submitListeningEvent({
        track_id: "demo-track-001",
        event_type: "started",
        position_ms: 0,
        idempotency_key: "demo-track-001:started",
      }),
    ).resolves.toMatchObject({ event_type: "started" });
  });

  it("calls player session mutations", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      text: async () =>
        JSON.stringify({
          state: "playing",
          active_track: null,
          queue: [],
          queue_index: null,
          volume: { level: 0.8 },
          shuffle: false,
          repeat_mode: "off",
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiClient.play("demo-track-001");
    await apiClient.queueTrack("demo-track-002");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/player/play",
      expect.objectContaining({ method: "PUT" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/player/queue",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("fetches recent blooms history", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () => JSON.stringify({ items: [] }),
      }),
    );

    await expect(apiClient.getRecentBlooms(20)).resolves.toEqual({ items: [] });
    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/history/recent?limit=20",
      expect.any(Object),
    );
  });

  it("manages favorite tracks", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ items: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiClient.getFavorites()).resolves.toEqual({ items: [] });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/favorites",
      expect.any(Object),
    );

    fetchMock.mockResolvedValueOnce({
      ok: true,
      text: async () =>
        JSON.stringify({
          id: 1,
          track_id: "demo-track-001",
          title: "Morning Dew Waltz",
          artist_name: "Petal & Pine",
          artwork: { local_path: "/static/demo/artwork/morning-dew-waltz.png" },
          duration_ms: 184000,
          playable_in_demo_mode: true,
          favorited_at: "2026-08-01T18:00:00Z",
        }),
    });
    await apiClient.addFavorite("demo-track-001");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/favorites/demo-track-001",
      expect.objectContaining({ method: "PUT" }),
    );

    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 204,
      text: async () => "",
    });
    await apiClient.removeFavorite("demo-track-001");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/favorites/demo-track-001",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});

describe("media helpers", () => {
  it("prefers local demo paths and flags unavailable hosts", () => {
    expect(
      resolveMediaPath({ local_path: "/static/demo/audio/morning-dew-waltz.wav" }),
    ).toBe("/static/demo/audio/morning-dew-waltz.wav");
    expect(
      resolveMediaPath({ url: "https://demo.musicbloom.local/audio/example.ogg" }),
    ).toBeNull();
    expect(
      getAudioAvailability({
        playable_in_demo_mode: true,
        audio: { local_path: "/static/demo/audio/morning-dew-waltz.wav" },
      }),
    ).toBe("available");
    expect(
      getAudioAvailability({
        playable_in_demo_mode: false,
        audio: { url: "https://example.com/audio.ogg" },
      }),
    ).toBe("preview-only");
  });
});
