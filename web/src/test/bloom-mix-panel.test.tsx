import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { apiClient } from "../api/client";
import type { ActiveTrack, PlayerSession, Track } from "../api/types";
import { BloomMixPanel } from "../components/player/BloomMixPanel";
import { generateBloomMix } from "../player/bloomMix";
import { planBloomMixPlant } from "../player/plantBloomMix";
import { PlayerProvider } from "../player/PlayerContext";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

function stubMediaElement() {
  Object.defineProperty(window.HTMLMediaElement.prototype, "load", {
    configurable: true,
    writable: true,
    value: function load(this: HTMLMediaElement) {
      queueMicrotask(() => {
        this.dispatchEvent(new Event("canplay"));
      });
    },
  });
  Object.defineProperty(window.HTMLMediaElement.prototype, "play", {
    configurable: true,
    writable: true,
    value: async function play() {
      return undefined;
    },
  });
  Object.defineProperty(window.HTMLMediaElement.prototype, "pause", {
    configurable: true,
    writable: true,
    value: function pause() {
      return undefined;
    },
  });

  class FakeAnalyserNode {
    fftSize = 256;
    connect() {
      return this;
    }
  }

  class FakeAudioContext {
    createMediaElementSource() {
      return {
        connect() {
          return this;
        },
      };
    }
    createAnalyser() {
      return new FakeAnalyserNode();
    }
    close() {
      return Promise.resolve();
    }
  }

  Object.defineProperty(window, "AudioContext", {
    configurable: true,
    writable: true,
    value: FakeAudioContext,
  });
}

function stubMatchMedia(reducedMotion: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches:
        query === "(prefers-reduced-motion: reduce)" ? reducedMotion : false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
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

const dreamyTracks: Track[] = [
  makeTrack({ id: "dreamy-a", title: "Cloud Terrace", mood: "dreamy" }),
  makeTrack({ id: "dreamy-b", title: "Moonlit Trellis", mood: "dreamy" }),
];

function buildActiveTrack(track: Track): ActiveTrack {
  return {
    track_id: track.id,
    title: track.title,
    artist_name: track.artist_name,
    album_title: track.album_title,
    duration_ms: track.duration_ms,
    artwork: track.artwork,
    audio: track.audio,
    mood: track.mood,
    genre: track.genre,
    accent_theme: track.accent_theme,
    playable_in_demo_mode: track.playable_in_demo_mode,
    position: { position_ms: 12_000 },
  };
}

function buildSession(
  overrides: Partial<PlayerSession> = {},
): PlayerSession {
  return {
    state: "stopped",
    active_track: null,
    queue: [],
    queue_index: null,
    volume: { level: 0.8 },
    shuffle: false,
    repeat_mode: "off",
    ...overrides,
  };
}

function mockCatalogTracks() {
  vi.spyOn(apiClient, "getTracks").mockImplementation(async (params) => {
    const mood = params?.mood;
    const items =
      mood === "dreamy"
        ? dreamyTracks
        : typeof mood === "string"
          ? calmTracks.filter((track) => track.mood === mood)
          : calmTracks;
    return {
      items,
      total: items.length,
      page: 1,
      page_size: 50,
      total_pages: 1,
    };
  });
}

function renderPanel(session: PlayerSession = buildSession()) {
  let currentSession = session;
  vi.spyOn(apiClient, "getPlayerSession").mockImplementation(async () => {
    return currentSession;
  });

  const playSpy = vi.spyOn(apiClient, "play").mockImplementation(async (trackId) => {
    const track =
      [...calmTracks, ...dreamyTracks].find((item) => item.id === trackId) ??
      calmTracks[0]!;
    currentSession = buildSession({
      ...currentSession,
      state: "playing",
      active_track: buildActiveTrack(track),
      queue: currentSession.queue,
      queue_index: null,
    });
    return currentSession;
  });

  const queueSpy = vi
    .spyOn(apiClient, "queueTrack")
    .mockImplementation(async (trackId) => {
      const track = [...calmTracks, ...dreamyTracks].find(
        (item) => item.id === trackId,
      );
      if (!track) {
        throw new Error(`Unknown track ${trackId}`);
      }
      currentSession = buildSession({
        ...currentSession,
        queue: [
          ...currentSession.queue,
          {
            track_id: track.id,
            title: track.title,
            artist_name: track.artist_name,
            duration_ms: track.duration_ms,
          },
        ],
      });
      return currentSession;
    });

  mockCatalogTracks();
  vi.spyOn(apiClient, "submitListeningEvent").mockResolvedValue({
    id: 1,
    idempotency_key: "demo",
    track_id: "calm-a",
    event_type: "started",
    position_ms: 0,
    occurred_at: new Date().toISOString(),
    awards: [],
    melody_points_earned: 0,
    experience_earned: 0,
    duplicate: false,
  });

  render(
    <QueryProvider client={createTestQueryClient()}>
      <PlayerProvider>
        <BloomMixPanel />
      </PlayerProvider>
    </QueryProvider>,
  );

  return { playSpy, queueSpy, getSession: () => currentSession };
}

async function selectCalmAndWaitForPreview() {
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: /Calm/i }));
  const preview = await screen.findByRole("list", {
    name: "BloomMix preview",
  });
  return { user, preview };
}

describe("planBloomMixPlant", () => {
  it("skips active and queued track IDs while preserving order", () => {
    const plan = planBloomMixPlant(["a", "b", "c", "d"], "b", ["d"]);

    expect(plan.toPlant).toEqual(["a", "c"]);
    expect(plan.skipped).toBe(2);
    expect(plan.startWithPlay).toBe(false);
  });

  it("starts with play when no track is active", () => {
    const plan = planBloomMixPlant(["a", "b"], null, []);
    expect(plan.startWithPlay).toBe(true);
    expect(plan.toPlant).toEqual(["a", "b"]);
  });
});

describe("BloomMixPanel", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubMediaElement();
    stubMatchMedia(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows every mood and an initial prompt before selection", async () => {
    renderPanel();

    expect(
      await screen.findByRole("group", { name: "BloomMix moods" }),
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
  });

  it("marks the selected mood as pressed and shows a Selected label", async () => {
    renderPanel();
    await selectCalmAndWaitForPreview();

    const calmButton = screen.getByRole("button", { name: /Calm/i });
    expect(calmButton).toHaveAttribute("aria-pressed", "true");
    expect(
      within(calmButton).getByText("Selected"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Playful/i }),
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("loads tracks for the selected mood and shows a successful preview", async () => {
    renderPanel();
    const { preview } = await selectCalmAndWaitForPreview();

    const items = within(preview).getAllByRole("listitem");
    expect(items).toHaveLength(5);
    expect(screen.getByRole("button", { name: "Plant this mix" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Refresh mix" })).toBeInTheDocument();
  });

  it("announces loading status through a polite live region", async () => {
    let resolveTracks: ((value: {
      items: Track[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }) => void) | undefined;

    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue(buildSession());
    vi.spyOn(apiClient, "getTracks").mockImplementation((params) => {
      if (params?.mood) {
        return new Promise((resolve) => {
          resolveTracks = resolve;
        });
      }
      return Promise.resolve({
        items: calmTracks,
        total: calmTracks.length,
        page: 1,
        page_size: 50,
        total_pages: 1,
      });
    });

    render(
      <QueryProvider client={createTestQueryClient()}>
        <PlayerProvider>
          <BloomMixPanel />
        </PlayerProvider>
      </QueryProvider>,
    );

    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /Dreamy/i }));

    const loadingStatus = await screen.findByRole("status");
    expect(loadingStatus).toHaveTextContent("Growing your BloomMix");
    expect(
      loadingStatus.closest(".bloom-mix__result"),
    ).toHaveAttribute("aria-live", "polite");

    resolveTracks?.({
      items: dreamyTracks,
      total: dreamyTracks.length,
      page: 1,
      page_size: 50,
      total_pages: 1,
    });

    expect(await screen.findByText("Cloud Terrace")).toBeInTheDocument();
  });

  it("ignores stale responses after quickly switching moods", async () => {
    let resolveDreamy: ((value: {
      items: Track[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }) => void) | undefined;

    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue(buildSession());
    vi.spyOn(apiClient, "getTracks").mockImplementation((params) => {
      if (params?.mood === "dreamy") {
        return new Promise((resolve) => {
          resolveDreamy = resolve;
        });
      }
      if (params?.mood === "calm") {
        return Promise.resolve({
          items: calmTracks,
          total: calmTracks.length,
          page: 1,
          page_size: 50,
          total_pages: 1,
        });
      }
      return Promise.resolve({
        items: calmTracks,
        total: calmTracks.length,
        page: 1,
        page_size: 50,
        total_pages: 1,
      });
    });

    render(
      <QueryProvider client={createTestQueryClient()}>
        <PlayerProvider>
          <BloomMixPanel />
        </PlayerProvider>
      </QueryProvider>,
    );

    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /Dreamy/i }));
    expect(
      await screen.findByText("Growing your BloomMix"),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Calm/i }));
    expect(
      await screen.findByRole("list", { name: "BloomMix preview" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Morning Dew Waltz")).toBeInTheDocument();

    resolveDreamy?.({
      items: dreamyTracks,
      total: dreamyTracks.length,
      page: 1,
      page_size: 50,
      total_pages: 1,
    });

    await waitFor(() => {
      expect(screen.queryByText("Cloud Terrace")).not.toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /Calm/i }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Morning Dew Waltz")).toBeInTheDocument();
  });

  it("refreshes the mix ordering without another mood catalog request", async () => {
    renderPanel();
    const { user, preview } = await selectCalmAndWaitForPreview();
    const getTracksSpy = apiClient.getTracks as unknown as ReturnType<
      typeof vi.fn
    >;
    const moodCallsAfterSelect = getTracksSpy.mock.calls.filter(
      (call) => call[0]?.mood === "calm",
    ).length;

    const firstOrder = within(preview)
      .getAllByRole("listitem")
      .map((item) => item.textContent);

    await user.click(screen.getByRole("button", { name: "Refresh mix" }));

    await waitFor(() => {
      const nextOrder = within(
        screen.getByRole("list", { name: "BloomMix preview" }),
      )
        .getAllByRole("listitem")
        .map((item) => item.textContent);
      expect(nextOrder).not.toEqual(firstOrder);
    });

    const moodCallsAfterRefresh = getTracksSpy.mock.calls.filter(
      (call) => call[0]?.mood === "calm",
    ).length;
    expect(moodCallsAfterRefresh).toBe(moodCallsAfterSelect);
  });

  it("shows an empty state when no playable tracks match", async () => {
    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue(buildSession());
    vi.spyOn(apiClient, "getTracks").mockImplementation(async (params) => {
      if (params?.mood === "calm") {
        return {
          items: [
            makeTrack({
              id: "calm-preview",
              title: "Ghostlight",
              mood: "calm",
              playable_in_demo_mode: false,
              audio: { url: "https://example.com/preview.ogg" },
            }),
          ],
          total: 1,
          page: 1,
          page_size: 50,
          total_pages: 1,
        };
      }
      return {
        items: calmTracks,
        total: calmTracks.length,
        page: 1,
        page_size: 50,
        total_pages: 1,
      };
    });

    render(
      <QueryProvider client={createTestQueryClient()}>
        <PlayerProvider>
          <BloomMixPanel />
        </PlayerProvider>
      </QueryProvider>,
    );

    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /Calm/i }));

    expect(
      await screen.findByText(
        /No playable tracks are available for this mood right now/i,
      ),
    ).toBeInTheDocument();
  });

  it("shows a helpful load error without raw server details", async () => {
    vi.spyOn(apiClient, "getPlayerSession").mockResolvedValue(buildSession());
    vi.spyOn(apiClient, "getTracks").mockImplementation(async (params) => {
      if (params?.mood) {
        throw new Error("SQLSTATE 57P01 terminating connection");
      }
      return {
        items: calmTracks,
        total: calmTracks.length,
        page: 1,
        page_size: 50,
        total_pages: 1,
      };
    });

    render(
      <QueryProvider client={createTestQueryClient()}>
        <PlayerProvider>
          <BloomMixPanel />
        </PlayerProvider>
      </QueryProvider>,
    );

    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /Mysterious/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/couldn't load tracks for this mood/i);
    expect(alert).not.toHaveTextContent(/SQLSTATE/i);
  });
});

describe("BloomMixPanel planting", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    stubMediaElement();
    stubMatchMedia(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("plays the first preview track and queues the rest in preview order when idle", async () => {
    const { playSpy, queueSpy } = renderPanel(buildSession());
    const { user, preview } = await selectCalmAndWaitForPreview();

    const previewIds = generateBloomMix(calmTracks, "calm", 1).map(
      (track) => track.id,
    );
    for (const id of previewIds) {
      const title = calmTracks.find((track) => track.id === id)?.title;
      expect(within(preview).getByText(title!)).toBeInTheDocument();
    }

    const sessionCallsBefore = (
      apiClient.getPlayerSession as unknown as ReturnType<typeof vi.fn>
    ).mock.calls.length;

    await user.click(screen.getByRole("button", { name: "Plant this mix" }));

    await waitFor(() => {
      expect(playSpy).toHaveBeenCalledWith(previewIds[0]);
    });
    expect(queueSpy.mock.calls.map((call) => call[0])).toEqual(
      previewIds.slice(1),
    );

    expect(
      await screen.findByText(/Planted 5 tracks into your garden queue/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Success:/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(
        (apiClient.getPlayerSession as unknown as ReturnType<typeof vi.fn>).mock
          .calls.length,
      ).toBeGreaterThan(sessionCallsBefore);
    });
  });

  it("shows planting celebration markup and reduced-motion panel class", async () => {
    stubMatchMedia(true);
    renderPanel(buildSession());
    const { user } = await selectCalmAndWaitForPreview();

    expect(
      document.querySelector(".bloom-mix-panel--reduced-motion"),
    ).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "Plant this mix" }));

    expect(
      await screen.findByText(/Planted 5 tracks into your garden queue/i),
    ).toBeInTheDocument();
    expect(document.querySelector(".bloom-mix__celebration")).not.toBeNull();
    expect(document.querySelector(".bloom-mix__sprout")).not.toBeNull();
  });

  it("keeps celebration markup when motion is allowed", async () => {
    stubMatchMedia(false);
    renderPanel(buildSession());
    const { user } = await selectCalmAndWaitForPreview();

    await waitFor(() => {
      expect(
        document.querySelector(".bloom-mix-panel--reduced-motion"),
      ).toBeNull();
    });

    await user.click(screen.getByRole("button", { name: "Plant this mix" }));

    expect(
      await screen.findByText(/Planted 5 tracks into your garden queue/i),
    ).toBeInTheDocument();
    expect(document.querySelector(".bloom-mix__celebration")).not.toBeNull();
  });

  it("appends only new tracks and preserves the active track while playing", async () => {
    const active = calmTracks[0]!;
    const alreadyQueued = calmTracks[1]!;
    const { playSpy, queueSpy } = renderPanel(
      buildSession({
        state: "playing",
        active_track: buildActiveTrack(active),
        queue: [
          {
            track_id: alreadyQueued.id,
            title: alreadyQueued.title,
            artist_name: alreadyQueued.artist_name,
            duration_ms: alreadyQueued.duration_ms,
          },
        ],
        queue_index: null,
      }),
    );

    const { user } = await selectCalmAndWaitForPreview();
    const previewIds = generateBloomMix(calmTracks, "calm", 1).map(
      (track) => track.id,
    );
    const expectedQueueIds = previewIds.filter(
      (id) => id !== active.id && id !== alreadyQueued.id,
    );

    await user.click(screen.getByRole("button", { name: "Plant this mix" }));

    await waitFor(() => {
      expect(queueSpy).toHaveBeenCalled();
    });

    expect(playSpy).not.toHaveBeenCalled();
    expect(queueSpy.mock.calls.map((call) => call[0])).toEqual(expectedQueueIds);
    expect(
      await screen.findByText(
        new RegExp(
          `Planted ${expectedQueueIds.length} tracks? into your garden queue`,
          "i",
        ),
      ),
    ).toBeInTheDocument();
  });

  it("explains when every preview track is already active or queued", async () => {
    const previewIds = generateBloomMix(calmTracks, "calm", 1).map(
      (track) => track.id,
    );
    const [activeId, ...queuedIds] = previewIds;
    const active = calmTracks.find((track) => track.id === activeId)!;

    const { playSpy, queueSpy } = renderPanel(
      buildSession({
        state: "playing",
        active_track: buildActiveTrack(active),
        queue: queuedIds.map((id) => {
          const track = calmTracks.find((item) => item.id === id)!;
          return {
            track_id: track.id,
            title: track.title,
            artist_name: track.artist_name,
            duration_ms: track.duration_ms,
          };
        }),
      }),
    );

    const { user } = await selectCalmAndWaitForPreview();
    await user.click(screen.getByRole("button", { name: "Plant this mix" }));

    expect(
      await screen.findByText(
        /Every track in this mix is already active or queued/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Note:/i)).toBeInTheDocument();
    expect(playSpy).not.toHaveBeenCalled();
    expect(queueSpy).not.toHaveBeenCalled();
  });

  it("reports a partial failure without claiming the whole mix was planted", async () => {
    const { playSpy, queueSpy } = renderPanel(buildSession());
    queueSpy.mockImplementation(async (trackId) => {
      if (queueSpy.mock.calls.length >= 2) {
        throw new Error("Queue service unavailable SQLSTATE 57P01");
      }
      const track = calmTracks.find((item) => item.id === trackId)!;
      return buildSession({
        state: "playing",
        active_track: buildActiveTrack(calmTracks[0]!),
        queue: [
          {
            track_id: track.id,
            title: track.title,
            artist_name: track.artist_name,
            duration_ms: track.duration_ms,
          },
        ],
      });
    });

    const { user } = await selectCalmAndWaitForPreview();
    await user.click(screen.getByRole("button", { name: "Plant this mix" }));

    await waitFor(() => {
      expect(playSpy).toHaveBeenCalled();
    });

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/Partial:/i);
    expect(alert).toHaveTextContent(/Added 2 tracks/i);
    expect(alert).toHaveTextContent(/could not be planted/i);
    expect(alert).not.toHaveTextContent(/Planted 5 tracks/i);
    expect(alert).not.toHaveTextContent(/SQLSTATE/i);
    expect(alert).not.toHaveTextContent(/Queue service unavailable/i);
  });

  it("prevents repeated clicks from submitting the same plant operation twice", async () => {
    let resolvePlay: ((session: PlayerSession) => void) | undefined;
    const { playSpy, queueSpy } = renderPanel(buildSession());
    playSpy.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePlay = resolve;
        }),
    );

    const { user } = await selectCalmAndWaitForPreview();
    const plantButton = screen.getByRole("button", { name: "Plant this mix" });

    await user.click(plantButton);
    await user.click(plantButton);
    await user.click(plantButton);

    expect(plantButton).toBeDisabled();
    expect(screen.getByRole("button", { name: /Calm/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Refresh mix" })).toBeDisabled();

    await waitFor(() => {
      expect(playSpy).toHaveBeenCalledTimes(1);
    });
    expect(queueSpy).not.toHaveBeenCalled();

    resolvePlay?.(
      buildSession({
        state: "playing",
        active_track: buildActiveTrack(calmTracks[0]!),
      }),
    );

    await waitFor(() => {
      expect(queueSpy.mock.calls.length).toBeGreaterThan(0);
    });
    expect(playSpy).toHaveBeenCalledTimes(1);
  });
});
