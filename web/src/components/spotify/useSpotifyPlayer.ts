import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import type { SpotifyPlayerSnapshot } from "../../api/spotifyPlayerTypes";

const SPOTIFY_PLAYER_KEY = ["spotify", "player"] as const;

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Spotify playback request failed.";
}

export function useSpotifyPlayer() {
  const queryClient = useQueryClient();

  const playerQuery = useQuery({
    queryKey: SPOTIFY_PLAYER_KEY,
    queryFn: () => apiClient.getSpotifyPlayer(),
    refetchInterval: 3_000,
  });

  const invalidate = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: SPOTIFY_PLAYER_KEY });
  }, [queryClient]);

  const runControl = useMutation({
    mutationFn: async (action: () => Promise<SpotifyPlayerSnapshot>) => {
      const snapshot = await action();
      queryClient.setQueryData(SPOTIFY_PLAYER_KEY, snapshot);
      return snapshot;
    },
  });

  const controlError =
    runControl.error !== null && runControl.error !== undefined
      ? getErrorMessage(runControl.error)
      : null;

  return {
    snapshot: playerQuery.data,
    isLoading: playerQuery.isLoading,
    isError: playerQuery.isError,
    errorMessage: playerQuery.error ? getErrorMessage(playerQuery.error) : null,
    controlError,
    isControlling: runControl.isPending,
    refresh: invalidate,
    play: () => {
      void runControl.mutateAsync(() => apiClient.spotifyPlay()).catch(() => undefined);
    },
    pause: () => {
      void runControl.mutateAsync(() => apiClient.spotifyPause()).catch(() => undefined);
    },
    next: () => {
      void runControl.mutateAsync(() => apiClient.spotifyNext()).catch(() => undefined);
    },
    previous: () => {
      void runControl.mutateAsync(() => apiClient.spotifyPrevious()).catch(
        () => undefined,
      );
    },
    seek: (positionMs: number) => {
      void runControl
        .mutateAsync(() => apiClient.spotifySeek(positionMs))
        .catch(() => undefined);
    },
    setVolume: (level: number) => {
      void runControl
        .mutateAsync(() => apiClient.spotifySetVolume(level))
        .catch(() => undefined);
    },
  };
}
