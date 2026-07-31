import { getAudioAvailability } from "../api/client";
import type { Track, TrackMood } from "../api/types";

const DEFAULT_MIX_SIZE = 5;

/** Mulberry32 — deterministic PRNG from a numeric seed. */
function createSeededRandom(seed: number): () => number {
  let state = seed >>> 0;

  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let next = Math.imul(state ^ (state >>> 15), 1 | state);
    next = (next + Math.imul(next ^ (next >>> 7), 61 | next)) ^ next;
    return ((next ^ (next >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffleWithSeed<T>(items: T[], seed: number): T[] {
  const shuffled = [...items];
  const random = createSeededRandom(seed);

  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(random() * (index + 1));
    const current = shuffled[index]!;
    shuffled[index] = shuffled[swapIndex]!;
    shuffled[swapIndex] = current;
  }

  return shuffled;
}

/**
 * Builds a mood-matched BloomMix queue from a track catalog.
 *
 * Only playable tracks for the selected mood are included. Duplicate IDs are
 * dropped, the input array is left untouched, and the seed controls ordering.
 */
export function generateBloomMix(
  tracks: readonly Track[],
  mood: TrackMood,
  seed: number,
  mixSize: number = DEFAULT_MIX_SIZE,
): Track[] {
  const seenIds = new Set<string>();
  const eligible: Track[] = [];

  for (const track of tracks) {
    if (track.mood !== mood) {
      continue;
    }

    if (getAudioAvailability(track) !== "available") {
      continue;
    }

    if (seenIds.has(track.id)) {
      continue;
    }

    seenIds.add(track.id);
    eligible.push(track);
  }

  const size = Math.max(0, Math.floor(mixSize));
  return shuffleWithSeed(eligible, seed).slice(0, size);
}
