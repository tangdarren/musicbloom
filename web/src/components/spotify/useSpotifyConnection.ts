import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import { buildApiUrl } from "../../config/env";
import type { SpotifyPanelState } from "../../api/spotifyTypes";

const SPOTIFY_STATUS_KEY = ["spotify", "status"] as const;

function resolvePanelState(
  status: Awaited<ReturnType<typeof apiClient.getSpotifyStatus>> | undefined,
  isConnecting: boolean,
): SpotifyPanelState {
  if (isConnecting) {
    return "connecting";
  }
  if (!status) {
    return "disconnected";
  }
  if (status.status === "connected") {
    return "connected";
  }
  if (status.status === "error") {
    return "error";
  }
  return "disconnected";
}

export function useSpotifyConnection() {
  const queryClient = useQueryClient();
  const statusQuery = useQuery({
    queryKey: SPOTIFY_STATUS_KEY,
    queryFn: () => apiClient.getSpotifyStatus(),
  });

  const disconnectMutation = useMutation({
    mutationFn: () => apiClient.disconnectSpotify(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: SPOTIFY_STATUS_KEY });
    },
  });

  const panelState = resolvePanelState(
    statusQuery.data,
    false,
  );

  const connect = () => {
    window.location.assign(buildApiUrl("/api/v1/auth/spotify/login"));
  };

  const disconnect = () => disconnectMutation.mutate();

  return {
    status: statusQuery.data,
    panelState,
    isLoading: statusQuery.isLoading,
    isDisconnecting: disconnectMutation.isPending,
    connect,
    disconnect,
    refresh: () => queryClient.invalidateQueries({ queryKey: SPOTIFY_STATUS_KEY }),
  };
}
