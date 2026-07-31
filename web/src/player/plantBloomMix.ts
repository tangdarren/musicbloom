export interface BloomMixPlantPlan {
  /** Preview track IDs to plant, preserving preview order. */
  toPlant: string[];
  /** How many preview tracks were skipped as already active or queued. */
  skipped: number;
  /**
   * When true, the first `toPlant` ID should start via play();
   * remaining IDs are appended with queueTrack().
   * When false, every `toPlant` ID is appended only.
   */
  startWithPlay: boolean;
}

/**
 * Decide which BloomMix preview tracks to plant and whether playback
 * should start with the first new track (no active track) or only append.
 */
export function planBloomMixPlant(
  previewTrackIds: readonly string[],
  activeTrackId: string | null,
  queueTrackIds: readonly string[],
): BloomMixPlantPlan {
  const occupied = new Set(queueTrackIds);
  if (activeTrackId) {
    occupied.add(activeTrackId);
  }

  const toPlant = previewTrackIds.filter((trackId) => !occupied.has(trackId));

  return {
    toPlant,
    skipped: previewTrackIds.length - toPlant.length,
    startWithPlay: activeTrackId === null && toPlant.length > 0,
  };
}
