import { describe, expect, it } from "vitest";

import {
  buildListeningIdempotencyKey,
  PROGRESS_REPORT_INTERVAL_MS,
} from "../player/listeningSync";

describe("listening sync helpers", () => {
  it("builds stable progress buckets", () => {
    expect(buildListeningIdempotencyKey("demo-track-001", "started", 0)).toBe(
      "demo-track-001:started",
    );
    expect(
      buildListeningIdempotencyKey("demo-track-001", "progress", 16_000),
    ).toBe("demo-track-001:progress:1");
  });

  it("uses a 15 second progress interval constant", () => {
    expect(PROGRESS_REPORT_INTERVAL_MS).toBe(15_000);
  });
});
