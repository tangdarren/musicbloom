import { buildApiUrl } from "../config/env";
import type {
  ActiveTrack,
  AudioSource,
  ListeningEventRecord,
  ListeningEventType,
  PaginatedTrackResponse,
  PlayerSession,
  RepeatMode,
  Track,
  TrackArtwork,
} from "./types";
import { ApiError, NetworkError } from "./types";

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const bodyText = await response.text();

  if (!response.ok) {
    throw new ApiError(
      `Request failed with status ${response.status}`,
      response.status,
      bodyText,
    );
  }

  if (!bodyText) {
    throw new ApiError("Empty response body", response.status, bodyText);
  }

  return JSON.parse(bodyText) as T;
}

async function apiRequest<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const url = buildApiUrl(path);

  try {
    const response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...init.headers,
      },
    });

    return parseJsonResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new NetworkError();
  }
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  return apiRequest<T>(path, { ...init, method: "GET" });
}

export async function apiPut<T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  const requestInit: RequestInit = {
    ...init,
    method: "PUT",
    headers,
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    requestInit.body = JSON.stringify(body);
  }

  return apiRequest<T>(path, requestInit);
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<T> {
  return apiRequest<T>(path, {
    ...init,
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export async function apiDelete<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  return apiRequest<T>(path, { ...init, method: "DELETE" });
}

export function resolveMediaPath(source: TrackArtwork | AudioSource): string | null {
  if (source.local_path) {
    return source.local_path;
  }

  if (source.url && !source.url.includes("demo.musicbloom.local")) {
    return source.url;
  }

  return null;
}

export function getAudioAvailability(
  track: Pick<ActiveTrack | Track, "playable_in_demo_mode" | "audio">,
): import("./types").AudioAvailability {
  if (!track.playable_in_demo_mode) {
    return "preview-only";
  }

  if (resolveMediaPath(track.audio)) {
    return "available";
  }

  return "unavailable";
}

export const apiClient = {
  getHealth: () => apiGet<import("./types").HealthResponse>("/api/health"),
  getRoot: () => apiGet<import("./types").RootResponse>("/"),
  getTracks: (params?: Record<string, string | number | undefined>) => {
    const search = new URLSearchParams();
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== "") {
          search.set(key, String(value));
        }
      }
    }
    const query = search.toString();
    return apiGet<PaginatedTrackResponse>(
      `/api/v1/tracks${query ? `?${query}` : ""}`,
    );
  },
  getTrack: (trackId: string) => apiGet<Track>(`/api/v1/tracks/${trackId}`),
  getPlayerSession: () => apiGet<PlayerSession>("/api/v1/player"),
  play: (trackId?: string) =>
    apiPut<PlayerSession>(
      "/api/v1/player/play",
      trackId ? { track_id: trackId } : undefined,
    ),
  pause: () => apiPut<PlayerSession>("/api/v1/player/pause"),
  seek: (positionMs: number) =>
    apiPut<PlayerSession>("/api/v1/player/seek", { position_ms: positionMs }),
  setVolume: (level: number) =>
    apiPut<PlayerSession>("/api/v1/player/volume", { level }),
  setShuffle: (enabled: boolean) =>
    apiPut<PlayerSession>("/api/v1/player/shuffle", { enabled }),
  setRepeat: (mode: RepeatMode) =>
    apiPut<PlayerSession>("/api/v1/player/repeat", { mode }),
  next: () => apiPost<PlayerSession>("/api/v1/player/next"),
  previous: () => apiPost<PlayerSession>("/api/v1/player/previous"),
  queueTrack: (trackId: string, allowDuplicate = false) =>
    apiPost<PlayerSession>("/api/v1/player/queue", {
      track_id: trackId,
      allow_duplicate: allowDuplicate,
    }),
  removeFromQueue: (trackId: string) =>
    apiDelete<PlayerSession>(`/api/v1/player/queue/${trackId}`),
  submitListeningEvent: (payload: {
    track_id: string;
    event_type: ListeningEventType;
    position_ms: number;
    idempotency_key: string;
  }) => apiPost<ListeningEventRecord>("/api/v1/listening/events", payload),
};
