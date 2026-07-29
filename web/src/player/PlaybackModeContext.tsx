import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type PlaybackMode = "demo" | "spotify";

const STORAGE_KEY = "musicbloom-playback-mode";

interface PlaybackModeContextValue {
  mode: PlaybackMode;
  setMode: (mode: PlaybackMode) => void;
}

const PlaybackModeContext = createContext<PlaybackModeContextValue | null>(null);

function readStoredMode(): PlaybackMode {
  if (typeof window === "undefined") {
    return "demo";
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === "spotify" ? "spotify" : "demo";
}

export function PlaybackModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<PlaybackMode>(() => readStoredMode());

  const setMode = useCallback((nextMode: PlaybackMode) => {
    setModeState(nextMode);
    window.localStorage.setItem(STORAGE_KEY, nextMode);
  }, []);

  const value = useMemo(
    () => ({
      mode,
      setMode,
    }),
    [mode, setMode],
  );

  return (
    <PlaybackModeContext.Provider value={value}>
      {children}
    </PlaybackModeContext.Provider>
  );
}

export function usePlaybackMode() {
  const context = useContext(PlaybackModeContext);
  if (!context) {
    throw new Error("usePlaybackMode must be used within PlaybackModeProvider");
  }
  return context;
}
