import type { TrackMood } from "../api/types";

export interface BloomMixMoodOption {
  id: TrackMood;
  name: string;
  description: string;
}

/** Readable labels for every catalog TrackMood used by BloomMix. */
export const BLOOM_MIX_MOODS: readonly BloomMixMoodOption[] = [
  {
    id: "calm",
    name: "Calm",
    description: "Soft garden ambience for quiet listening.",
  },
  {
    id: "playful",
    name: "Playful",
    description: "Bright, bouncing tunes to lift your spirits.",
  },
  {
    id: "dreamy",
    name: "Dreamy",
    description: "Hazy soundscapes for slow wandering.",
  },
  {
    id: "energetic",
    name: "Energetic",
    description: "Upbeat tracks to wake the greenhouse.",
  },
  {
    id: "cozy",
    name: "Cozy",
    description: "Warm, intimate songs for settled evenings.",
  },
  {
    id: "mysterious",
    name: "Mysterious",
    description: "Shadowy melodies among the vines.",
  },
] as const;
