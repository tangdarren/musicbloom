import { describe, expect, it } from "vitest";

import type { Track, TrackMood } from "../api/types";
import { generateBloomMix } from "../player/bloomMix";

function makeTrack(
  overrides: Partial<Track> & Pick<Track, "id" | "mood">,
): Track {
  return {
    title: overrides.title ?? overrides.id,
    artist_id: "artist-petal-pine",
    artist_name: "Petal & Pine",
    album_id: "album-greenhouse-echoes",
    album_title: "Greenhouse Echoes",
    duration_ms: 180_000,
    artwork: { local_path: "/static/demo/artwork/example.png" },
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

const catalog: Track[] = [
  makeTrack({ id: "calm-a", mood: "calm" }),
  makeTrack({ id: "calm-b", mood: "calm" }),
  makeTrack({ id: "calm-c", mood: "calm" }),
  makeTrack({ id: "calm-d", mood: "calm" }),
  makeTrack({ id: "calm-e", mood: "calm" }),
  makeTrack({ id: "calm-f", mood: "calm" }),
  makeTrack({ id: "playful-a", mood: "playful" }),
  makeTrack({ id: "dreamy-a", mood: "dreamy" }),
  makeTrack({
    id: "calm-preview",
    mood: "calm",
    playable_in_demo_mode: false,
    audio: { url: "https://example.com/preview.ogg" },
  }),
  makeTrack({
    id: "calm-unavailable",
    mood: "calm",
    audio: { url: "https://demo.musicbloom.local/audio/missing.ogg" },
  }),
];

describe("generateBloomMix", () => {
  it("only returns tracks matching the selected mood", () => {
    const mix = generateBloomMix(catalog, "calm", 1);

    expect(mix.length).toBeGreaterThan(0);
    expect(mix.every((track) => track.mood === "calm")).toBe(true);
    expect(mix.some((track) => track.id.startsWith("playful"))).toBe(false);
  });

  it("prevents duplicate track IDs", () => {
    const withDuplicates: Track[] = [
      makeTrack({ id: "calm-a", mood: "calm" }),
      makeTrack({ id: "calm-a", mood: "calm", title: "Duplicate Calm A" }),
      makeTrack({ id: "calm-b", mood: "calm" }),
    ];

    const mix = generateBloomMix(withDuplicates, "calm", 7);

    expect(mix.map((track) => track.id)).toEqual(
      expect.arrayContaining(["calm-a", "calm-b"]),
    );
    expect(new Set(mix.map((track) => track.id)).size).toBe(mix.length);
    expect(mix).toHaveLength(2);
  });

  it("excludes tracks that cannot be played", () => {
    const mix = generateBloomMix(catalog, "calm", 3);
    const ids = mix.map((track) => track.id);

    expect(ids).not.toContain("calm-preview");
    expect(ids).not.toContain("calm-unavailable");
    expect(
      mix.every((track) => track.playable_in_demo_mode),
    ).toBe(true);
  });

  it("caps the mix at the maximum size of five by default", () => {
    const mix = generateBloomMix(catalog, "calm", 11);

    expect(mix).toHaveLength(5);
  });

  it("respects a custom mix size", () => {
    const mix = generateBloomMix(catalog, "calm", 11, 3);

    expect(mix).toHaveLength(3);
  });

  it("returns fewer than five tracks when fewer are available", () => {
    const sparse: Track[] = [
      makeTrack({ id: "playful-a", mood: "playful" }),
      makeTrack({ id: "playful-b", mood: "playful" }),
    ];

    const mix = generateBloomMix(sparse, "playful", 4);

    expect(mix).toHaveLength(2);
  });

  it("returns an empty mix when no eligible tracks match", () => {
    const emptyMood: TrackMood = "mysterious";
    const mix = generateBloomMix(catalog, emptyMood, 9);

    expect(mix).toEqual([]);
  });

  it("produces the same ordering for the same seed and track list", () => {
    const first = generateBloomMix(catalog, "calm", 42);
    const second = generateBloomMix(catalog, "calm", 42);

    expect(first.map((track) => track.id)).toEqual(
      second.map((track) => track.id),
    );
  });

  it("can produce a different ordering for a different seed", () => {
    const first = generateBloomMix(catalog, "calm", 1);
    const second = generateBloomMix(catalog, "calm", 99);

    expect(first.map((track) => track.id)).not.toEqual(
      second.map((track) => track.id),
    );
  });

  it("does not modify the input track array", () => {
    const input = catalog.map((track) => ({ ...track }));
    const snapshot = structuredClone(input);

    generateBloomMix(input, "calm", 5);

    expect(input).toEqual(snapshot);
  });
});
