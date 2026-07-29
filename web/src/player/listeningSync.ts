import type { ListeningEventType } from "../api/types";
import { positionBucket } from "./format";

export function buildListeningIdempotencyKey(
  trackId: string,
  eventType: ListeningEventType,
  positionMs: number,
): string {
  if (eventType === "progress") {
    return `${trackId}:progress:${positionBucket(positionMs)}`;
  }

  return `${trackId}:${eventType}`;
}

export const PROGRESS_REPORT_INTERVAL_MS = 15_000;
