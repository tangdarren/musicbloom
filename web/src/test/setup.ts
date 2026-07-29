import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      text: async () =>
        JSON.stringify({ status: "healthy", service: "musicbloom-api" }),
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});
