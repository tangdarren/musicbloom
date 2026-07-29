import {
  createContext,
  useContext,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../api/client";
import type { PlaybackState } from "../api/types";

interface PlaybackSignalsValue {
  playbackState: PlaybackState;
  isPlaying: boolean;
  isPaused: boolean;
}

const PlaybackSignalsContext = createContext<PlaybackSignalsValue>({
  playbackState: "stopped",
  isPlaying: false,
  isPaused: false,
});

const PLAYER_POLL_KEY = ["player", "signals"] as const;

function subscribeToReducedMotion(onStoreChange: () => void) {
  const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  mediaQuery.addEventListener("change", onStoreChange);
  return () => mediaQuery.removeEventListener("change", onStoreChange);
}

function getReducedMotionSnapshot() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function getReducedMotionServerSnapshot() {
  return false;
}

export function PlaybackSignalsProvider({ children }: { children: ReactNode }) {
  const { data: session } = useQuery({
    queryKey: PLAYER_POLL_KEY,
    queryFn: () => apiClient.getPlayerSession(),
    refetchInterval: 3000,
    refetchIntervalInBackground: false,
  });

  const playbackState = session?.state ?? "stopped";
  const value: PlaybackSignalsValue = {
    playbackState,
    isPlaying: playbackState === "playing",
    isPaused: playbackState === "paused",
  };

  return (
    <PlaybackSignalsContext.Provider value={value}>
      {children}
    </PlaybackSignalsContext.Provider>
  );
}

export function usePlaybackSignals() {
  return useContext(PlaybackSignalsContext);
}

export function usePrefersReducedMotion() {
  return useSyncExternalStore(
    subscribeToReducedMotion,
    getReducedMotionSnapshot,
    getReducedMotionServerSnapshot,
  );
}
