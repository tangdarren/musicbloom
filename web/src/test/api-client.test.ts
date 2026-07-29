import { describe, expect, it, vi } from "vitest";

import { apiClient } from "../api/client";
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
});
