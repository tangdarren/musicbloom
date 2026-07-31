import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  apiClient,
  getAudioAvailability,
  resolveMediaPath,
} from "../api/client";
import type {
  ActiveTrack,
  ListeningEventRecord,
  PlayerSession,
  RepeatMode,
  Track,
} from "../api/types";
import { clamp } from "./format";
import {
  buildListeningIdempotencyKey,
  PROGRESS_REPORT_INTERVAL_MS,
} from "./listeningSync";

const PLAYER_SESSION_KEY = ["player", "session"] as const;
const TRACK_CATALOG_KEY = ["catalog", "tracks"] as const;

interface PlayerContextValue {
  session: PlayerSession | undefined;
  tracks: Track[];
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  localPositionMs: number;
  audioAvailable: boolean;
  audioError: string | null;
  lastListeningEvent: ListeningEventRecord | null;
  recentAwards: string[];
  playTrack: (trackId: string) => Promise<void>;
  togglePlayPause: () => Promise<void>;
  seekTo: (positionMs: number) => Promise<void>;
  changeVolume: (level: number) => Promise<void>;
  toggleShuffle: () => Promise<void>;
  cycleRepeat: () => Promise<void>;
  skipNext: () => Promise<void>;
  skipPrevious: () => Promise<void>;
  enqueueTrack: (trackId: string) => Promise<void>;
  removeQueuedTrack: (trackId: string) => Promise<void>;
  analyser: AnalyserNode | null;
  isPlaying: boolean;
  activeTrack: ActiveTrack | null;
}

const PlayerContext = createContext<PlayerContextValue | null>(null);

const REPEAT_ORDER: RepeatMode[] = ["off", "all", "one"];

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while talking to the player API.";
}

async function loadAudioSource(
  audio: HTMLAudioElement,
  track: ActiveTrack,
): Promise<boolean> {
  const source = resolveMediaPath(track.audio);
  if (!source) {
    audio.removeAttribute("src");
    audio.load();
    return false;
  }

  const nextSrc = new URL(source, window.location.origin).href;
  if (audio.src === nextSrc && audio.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
    return true;
  }

  return new Promise((resolve) => {
    const handleCanPlay = () => {
      cleanup();
      resolve(true);
    };
    const handleError = () => {
      cleanup();
      resolve(false);
    };
    const cleanup = () => {
      audio.removeEventListener("canplay", handleCanPlay);
      audio.removeEventListener("error", handleError);
    };

    audio.addEventListener("canplay", handleCanPlay);
    audio.addEventListener("error", handleError);

    if (audio.src !== nextSrc) {
      audio.src = source;
      audio.load();
    } else {
      audio.load();
    }
  });
}

export function PlayerProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceConnectedRef = useRef(false);
  const progressIntervalRef = useRef<number | null>(null);
  const lastProgressBucketRef = useRef<number | null>(null);
  const startedTrackRef = useRef<string | null>(null);

  const [localPositionMs, setLocalPositionMs] = useState(0);
  const [audioAvailable, setAudioAvailable] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [lastListeningEvent, setLastListeningEvent] =
    useState<ListeningEventRecord | null>(null);
  const [recentAwards, setRecentAwards] = useState<string[]>([]);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);

  const sessionQuery = useQuery({
    queryKey: PLAYER_SESSION_KEY,
    queryFn: () => apiClient.getPlayerSession(),
  });

  const tracksQuery = useQuery({
    queryKey: TRACK_CATALOG_KEY,
    queryFn: () => apiClient.getTracks({ page: 1, page_size: 20 }),
  });

  const reportListeningEvent = useCallback(
    async (
      trackId: string,
      eventType: ListeningEventRecord["event_type"],
      positionMs: number,
    ) => {
      try {
        const record = await apiClient.submitListeningEvent({
          track_id: trackId,
          event_type: eventType,
          position_ms: positionMs,
          idempotency_key: buildListeningIdempotencyKey(
            trackId,
            eventType,
            positionMs,
          ),
        });
        setLastListeningEvent(record);
        if (record.awards.length > 0) {
          setRecentAwards(
            record.awards.map((award) => award.explanation).slice(0, 3),
          );
        }
      } catch {
        // Listening awards are best-effort; playback should continue.
      }
    },
    [],
  );

  const syncAudioToSession = useCallback(
    async (session: PlayerSession, shouldPlay: boolean) => {
      const audio = audioRef.current;
      const track = session.active_track;
      if (!audio || !track) {
        setAudioAvailable(false);
        setAudioError(null);
        return;
      }

      const availability = getAudioAvailability(track);
      if (availability !== "available") {
        setAudioAvailable(false);
        setAudioError(
          availability === "preview-only"
            ? "This track is preview-only in demo mode."
            : "Demo audio is unavailable for this track.",
        );
        return;
      }

      const loaded = await loadAudioSource(audio, track);
      if (!loaded) {
        setAudioAvailable(false);
        setAudioError("Demo audio file could not be loaded.");
        return;
      }

      if (!sourceConnectedRef.current) {
        audioContextRef.current ??= new AudioContext();
        const source = audioContextRef.current.createMediaElementSource(audio);
        const analyser = audioContextRef.current.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyser.connect(audioContextRef.current.destination);
        analyserRef.current = analyser;
        setAnalyserNode(analyser);
        sourceConnectedRef.current = true;
      }

      audio.volume = session.volume.level;
      audio.currentTime = track.position.position_ms / 1000;
      setLocalPositionMs(track.position.position_ms);
      setAudioAvailable(true);
      setAudioError(null);

      if (shouldPlay && session.state === "playing") {
        try {
          await audio.play();
          if (startedTrackRef.current !== track.track_id) {
            startedTrackRef.current = track.track_id;
            lastProgressBucketRef.current = null;
            await reportListeningEvent(track.track_id, "started", 0);
          }
        } catch {
          setAudioError("Playback requires a click on play.");
        }
      } else {
        audio.pause();
      }
    },
    [reportListeningEvent],
  );

  const runMutation = useCallback(
    async (updater: () => Promise<PlayerSession>, shouldPlay = false) => {
      const session = await updater();
      queryClient.setQueryData(PLAYER_SESSION_KEY, session);
      await syncAudioToSession(session, shouldPlay);
      return session;
    },
    [queryClient, syncAudioToSession],
  );

  const playMutation = useMutation({
    mutationFn: (trackId?: string) =>
      runMutation(() => apiClient.play(trackId), true),
  });

  const pauseMutation = useMutation({
    mutationFn: () => runMutation(() => apiClient.pause()),
  });

  const seekMutation = useMutation({
    mutationFn: (positionMs: number) =>
      runMutation(() => apiClient.seek(positionMs)),
  });

  const volumeMutation = useMutation({
    mutationFn: (level: number) =>
      runMutation(() => apiClient.setVolume(level)),
  });

  const shuffleMutation = useMutation({
    mutationFn: (enabled: boolean) =>
      runMutation(() => apiClient.setShuffle(enabled)),
  });

  const repeatMutation = useMutation({
    mutationFn: (mode: RepeatMode) =>
      runMutation(() => apiClient.setRepeat(mode)),
  });

  const nextMutation = useMutation({
    mutationFn: () => runMutation(() => apiClient.next(), true),
  });

  const previousMutation = useMutation({
    mutationFn: () => runMutation(() => apiClient.previous(), true),
  });

  const queueMutation = useMutation({
    mutationFn: (trackId: string) =>
      runMutation(() => apiClient.queueTrack(trackId)),
  });

  const removeQueueMutation = useMutation({
    mutationFn: (trackId: string) =>
      runMutation(() => apiClient.removeFromQueue(trackId)),
  });

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const handleTimeUpdate = () => {
      setLocalPositionMs(Math.floor(audio.currentTime * 1000));
    };

    const handleEnded = async () => {
      const track = sessionQuery.data?.active_track;
      if (!track) {
        return;
      }

      const positionMs = Math.min(
        track.duration_ms,
        Math.floor(audio.duration * 1000) || track.duration_ms,
      );
      await reportListeningEvent(track.track_id, "completed", positionMs);
      await nextMutation.mutateAsync();
    };

    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [nextMutation, reportListeningEvent, sessionQuery.data?.active_track]);

  useEffect(() => {
    if (sessionQuery.data?.state !== "playing" || !sessionQuery.data.active_track) {
      if (progressIntervalRef.current !== null) {
        window.clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
      return;
    }

    const track = sessionQuery.data.active_track;
    progressIntervalRef.current = window.setInterval(() => {
      const audio = audioRef.current;
      if (!audio || sessionQuery.data?.state !== "playing") {
        return;
      }

      const positionMs = Math.floor(audio.currentTime * 1000);
      const bucket = Math.floor(positionMs / PROGRESS_REPORT_INTERVAL_MS);
      if (lastProgressBucketRef.current === bucket) {
        return;
      }

      lastProgressBucketRef.current = bucket;
      void reportListeningEvent(track.track_id, "progress", positionMs);
    }, PROGRESS_REPORT_INTERVAL_MS);

    return () => {
      if (progressIntervalRef.current !== null) {
        window.clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    };
  }, [
    reportListeningEvent,
    sessionQuery.data?.active_track,
    sessionQuery.data?.state,
  ]);

  useEffect(() => {
    return () => {
      if (progressIntervalRef.current !== null) {
        window.clearInterval(progressIntervalRef.current);
      }
      void audioContextRef.current?.close();
    };
  }, []);

  const playTrack = useCallback(
    async (trackId: string) => {
      await playMutation.mutateAsync(trackId);
    },
    [playMutation],
  );

  const togglePlayPause = useCallback(async () => {
    const session = sessionQuery.data;
    if (!session?.active_track) {
      await playMutation.mutateAsync(undefined);
      return;
    }

    if (session.state === "playing") {
      audioRef.current?.pause();
      await pauseMutation.mutateAsync();
      return;
    }

    await playMutation.mutateAsync(undefined);
  }, [pauseMutation, playMutation, sessionQuery.data]);

  const seekTo = useCallback(
    async (positionMs: number) => {
      const track = sessionQuery.data?.active_track;
      if (!track) {
        return;
      }

      const clamped = clamp(positionMs, 0, track.duration_ms);
      if (audioRef.current && audioAvailable) {
        audioRef.current.currentTime = clamped / 1000;
      }
      setLocalPositionMs(clamped);
      await seekMutation.mutateAsync(clamped);
    },
    [audioAvailable, seekMutation, sessionQuery.data?.active_track],
  );

  const changeVolume = useCallback(
    async (level: number) => {
      const clamped = clamp(level, 0, 1);
      if (audioRef.current) {
        audioRef.current.volume = clamped;
      }
      await volumeMutation.mutateAsync(clamped);
    },
    [volumeMutation],
  );

  const toggleShuffle = useCallback(async () => {
    const enabled = !(sessionQuery.data?.shuffle ?? false);
    await shuffleMutation.mutateAsync(enabled);
  }, [sessionQuery.data?.shuffle, shuffleMutation]);

  const cycleRepeat = useCallback(async () => {
    const current = sessionQuery.data?.repeat_mode ?? "off";
    const nextIndex = (REPEAT_ORDER.indexOf(current) + 1) % REPEAT_ORDER.length;
    await repeatMutation.mutateAsync(REPEAT_ORDER[nextIndex] ?? "off");
  }, [repeatMutation, sessionQuery.data?.repeat_mode]);

  const skipNext = useCallback(async () => {
    const track = sessionQuery.data?.active_track;
    const audio = audioRef.current;
    if (track && audio) {
      await reportListeningEvent(
        track.track_id,
        "skipped",
        Math.floor(audio.currentTime * 1000),
      );
    }
    startedTrackRef.current = null;
    await nextMutation.mutateAsync();
  }, [nextMutation, reportListeningEvent, sessionQuery.data?.active_track]);

  const skipPrevious = useCallback(async () => {
    startedTrackRef.current = null;
    await previousMutation.mutateAsync();
  }, [previousMutation]);

  const enqueueTrack = useCallback(
    async (trackId: string) => {
      await queueMutation.mutateAsync(trackId);
    },
    [queueMutation],
  );

  const removeQueuedTrack = useCallback(
    async (trackId: string) => {
      await removeQueueMutation.mutateAsync(trackId);
    },
    [removeQueueMutation],
  );

  const session = sessionQuery.data;
  const value = useMemo<PlayerContextValue>(
    () => ({
      session,
      tracks: tracksQuery.data?.items ?? [],
      isLoading: sessionQuery.isLoading || tracksQuery.isLoading,
      isError: sessionQuery.isError || tracksQuery.isError,
      errorMessage:
        sessionQuery.error || tracksQuery.error
          ? getErrorMessage(sessionQuery.error ?? tracksQuery.error)
          : null,
      localPositionMs,
      audioAvailable,
      audioError,
      lastListeningEvent,
      recentAwards,
      playTrack,
      togglePlayPause,
      seekTo,
      changeVolume,
      toggleShuffle,
      cycleRepeat,
      skipNext,
      skipPrevious,
      enqueueTrack,
      removeQueuedTrack,
      analyser: analyserNode,
      isPlaying: session?.state === "playing",
      activeTrack: session?.active_track ?? null,
    }),
    [
      analyserNode,
      audioAvailable,
      audioError,
      changeVolume,
      cycleRepeat,
      enqueueTrack,
      lastListeningEvent,
      localPositionMs,
      playTrack,
      recentAwards,
      removeQueuedTrack,
      seekTo,
      session,
      sessionQuery.error,
      sessionQuery.isError,
      sessionQuery.isLoading,
      skipNext,
      skipPrevious,
      togglePlayPause,
      toggleShuffle,
      tracksQuery.data?.items,
      tracksQuery.error,
      tracksQuery.isError,
      tracksQuery.isLoading,
    ],
  );

  return (
    <PlayerContext.Provider value={value}>
      <audio ref={audioRef} preload="metadata" />
      {children}
    </PlayerContext.Provider>
  );
}

export { PlayerContext, PLAYER_SESSION_KEY, TRACK_CATALOG_KEY };
