import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../api/client";
import type { RecentBloomItem } from "../api/types";
import { HistoryPage } from "../pages/HistoryPage";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

const bloomItems: RecentBloomItem[] = [
  {
    id: 3,
    track_id: "demo-track-002",
    title: "Sunbeam Carousel",
    artist_name: "Greenhouse Quartet",
    artwork: { local_path: "/static/demo/artwork/sunbeam-carousel.png" },
    listening_status: "skipped",
    occurred_at: "2026-08-01T18:30:00Z",
  },
  {
    id: 2,
    track_id: "demo-track-001",
    title: "Morning Dew Waltz",
    artist_name: "Petal & Pine",
    artwork: { local_path: "/static/demo/artwork/morning-dew-waltz.png" },
    listening_status: "completed",
    occurred_at: "2026-08-01T16:05:00Z",
  },
  {
    id: 1,
    track_id: "demo-track-001",
    title: "Morning Dew Waltz",
    artist_name: "Petal & Pine",
    artwork: { local_path: "/static/demo/artwork/morning-dew-waltz.png" },
    listening_status: "played",
    occurred_at: "2026-07-31T21:10:00Z",
  },
];

function renderHistory() {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <HistoryPage />
    </QueryProvider>,
  );
}

describe("HistoryPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows an empty state when there is no listening history", async () => {
    vi.spyOn(apiClient, "getRecentBlooms").mockResolvedValue({ items: [] });

    renderHistory();

    expect(
      await screen.findByRole("heading", { name: "Listening history" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText(/No blooms yet/i),
    ).toBeInTheDocument();
  });

  it("groups blooms by date and distinguishes listening statuses", async () => {
    vi.spyOn(apiClient, "getRecentBlooms").mockResolvedValue({
      items: bloomItems,
    });

    renderHistory();

    expect(await screen.findByText("Sunbeam Carousel")).toBeInTheDocument();
    expect(screen.getAllByText("Morning Dew Waltz")).toHaveLength(2);
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Played")).toBeInTheDocument();
    expect(screen.getByText("Skipped")).toBeInTheDocument();

    const daySections = screen.getAllByRole("heading", { level: 2 });
    expect(daySections.length).toBeGreaterThanOrEqual(2);
    expect(
      within(daySections[0]!.closest("section")!).getByText("Sunbeam Carousel"),
    ).toBeInTheDocument();
  });

  it("shows a loading state while history is fetching", async () => {
    vi.spyOn(apiClient, "getRecentBlooms").mockImplementation(
      () => new Promise(() => undefined),
    );

    renderHistory();

    expect(
      await screen.findByText("Gathering recent blooms"),
    ).toBeInTheDocument();
  });

  it("shows an error state when the history request fails", async () => {
    vi.spyOn(apiClient, "getRecentBlooms").mockRejectedValue(
      new Error("History unavailable"),
    );

    renderHistory();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Unable to load listening history/i,
    );
  });
});
