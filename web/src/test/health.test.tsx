import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HealthIndicator } from "../components/HealthIndicator";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

describe("HealthIndicator", () => {
  it("shows a healthy status when the API responds", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () =>
          JSON.stringify({ status: "healthy", service: "musicbloom-api" }),
      }),
    );

    render(
      <QueryProvider client={createTestQueryClient()}>
        <HealthIndicator />
      </QueryProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/API healthy/i);
    });
  });

  it("shows an offline status when the API request fails", async () => {
    vi.unstubAllGlobals();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    render(
      <QueryProvider client={createTestQueryClient()}>
        <HealthIndicator />
      </QueryProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/API offline/i);
    });
  });
});
