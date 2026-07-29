import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { apiClient } from "../api/client";
import { SpotifyConnectionPanel } from "../components/spotify/SpotifyConnectionPanel";
import { QueryProvider } from "../providers/QueryProvider";
import { createTestQueryClient } from "./test-utils";

const disconnectedUnconfigured = {
  status: "disconnected" as const,
  configured: false,
  display_name: null,
  spotify_user_id: null,
  scopes: [],
  expires_at: null,
  error_code: null,
  error_message: null,
};

const connectedStatus = {
  status: "connected" as const,
  configured: true,
  display_name: "Bloom Listener",
  spotify_user_id: "spotify-user-123",
  scopes: ["user-read-email"],
  expires_at: "2026-01-01T00:00:00Z",
  error_code: null,
  error_message: null,
};

describe("SpotifyConnectionPanel", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows demo-friendly disconnected state when Spotify is not configured", () => {
    render(
      <SpotifyConnectionPanel
        status={disconnectedUnconfigured}
        panelState="disconnected"
        isLoading={false}
        isDisconnecting={false}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: "Spotify optional" })).toBeInTheDocument();
    expect(
      screen.getByText(/Demo mode works without Spotify credentials/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Connect Spotify" }),
    ).not.toBeInTheDocument();
  });

  it("shows connected state and disconnect action", async () => {
    const user = userEvent.setup();
    const onDisconnect = vi.fn();

    render(
      <SpotifyConnectionPanel
        status={connectedStatus}
        panelState="connected"
        isLoading={false}
        isDisconnecting={false}
        onConnect={vi.fn()}
        onDisconnect={onDisconnect}
      />,
    );

    expect(screen.getByText(/Bloom Listener is linked/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Disconnect Spotify" }));
    expect(onDisconnect).toHaveBeenCalled();
  });
});

describe("spotify status hook integration", () => {
  beforeEach(() => {
    vi.spyOn(apiClient, "getSpotifyStatus").mockResolvedValue({
      ...disconnectedUnconfigured,
      configured: true,
    });
  });

  it("loads configured disconnected status from the API", async () => {
    const { useSpotifyConnection } = await import(
      "../components/spotify/useSpotifyConnection"
    );

    function Probe() {
      const { status, panelState } = useSpotifyConnection();
      return (
        <div>
          <span>{panelState}</span>
          <span>{status?.configured ? "configured" : "unconfigured"}</span>
        </div>
      );
    }

    render(
      <QueryProvider client={createTestQueryClient()}>
        <Probe />
      </QueryProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("configured")).toBeInTheDocument();
    });
    expect(screen.getByText("disconnected")).toBeInTheDocument();
  });
});
