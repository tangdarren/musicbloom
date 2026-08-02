import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { apiClient } from "../api/client";
import { AppShell } from "../components/AppShell";
import { FavoriteToggleButton } from "../components/player/FavoriteToggleButton";
import { PlayerControls } from "../components/player/PlayerControls";
import { TopNav } from "../components/TopNav";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

describe("responsive and accessibility maintenance", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(apiClient, "getHealth").mockResolvedValue({
      status: "healthy",
      service: "musicbloom",
    });
  });

  it("exposes a skip link to main content", () => {
    render(
      <QueryProvider client={createTestQueryClient()}>
        <MemoryRouter>
          <AppShell />
        </MemoryRouter>
      </QueryProvider>,
    );

    const skipLink = screen.getByRole("link", { name: "Skip to main content" });
    expect(skipLink).toHaveAttribute("href", "#main-content");
    expect(document.getElementById("main-content")).not.toBeNull();
  });

  it("keeps primary navigation links keyboard-accessible", () => {
    render(
      <QueryProvider client={createTestQueryClient()}>
        <MemoryRouter>
          <TopNav />
        </MemoryRouter>
      </QueryProvider>,
    );

    const nav = screen.getByRole("navigation", { name: "Primary" });
    const links = screen.getAllByRole("link").filter((link) =>
      nav.contains(link),
    );

    expect(links.length).toBeGreaterThanOrEqual(7);
    for (const link of links) {
      expect(link).not.toHaveAttribute("tabindex", "-1");
      expect(link.textContent?.trim().length).toBeGreaterThan(0);
    }
  });

  it("labels icon-only favorite and transport controls", () => {
    render(
      <>
        <FavoriteToggleButton
          trackTitle="Morning Dew Waltz"
          isFavorited={false}
          onToggle={() => undefined}
        />
        <PlayerControls
          isPlaying={false}
          shuffle={false}
          repeatMode="off"
          onTogglePlayPause={() => undefined}
          onPrevious={() => undefined}
          onNext={() => undefined}
          onToggleShuffle={() => undefined}
          onCycleRepeat={() => undefined}
        />
      </>,
    );

    expect(
      screen.getByRole("button", { name: "Add Morning Dew Waltz to favorites" }),
    ).toHaveAttribute("aria-pressed", "false");
    expect(
      screen.getByRole("button", { name: "Previous track" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Next track" }),
    ).toBeInTheDocument();
  });

  it("marks disabled playback controls clearly for assistive tech", () => {
    render(
      <PlayerControls
        isPlaying={false}
        shuffle={false}
        repeatMode="off"
        disabled
        onTogglePlayPause={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        onToggleShuffle={() => undefined}
        onCycleRepeat={() => undefined}
      />,
    );

    expect(screen.getByRole("button", { name: "Start playback" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Previous track" })).toBeDisabled();
  });
});
