/** Typed API response models for the MusicBloom backend. */

export interface HealthResponse {
  status: string;
  service: string;
}

export interface RootResponse {
  name: string;
  tagline: string;
  version: string;
}

export type TrackMood =
  | "calm"
  | "playful"
  | "dreamy"
  | "energetic"
  | "cozy"
  | "mysterious";

export type PlaybackState = "playing" | "paused" | "stopped";
export type RepeatMode = "off" | "one" | "all";

export type ListeningEventType =
  | "started"
  | "progress"
  | "completed"
  | "skipped";

export interface TrackArtwork {
  url?: string;
  local_path?: string;
}

export interface AudioSource {
  url?: string;
  local_path?: string;
}

export interface AccentTheme {
  primary: string;
  secondary: string;
  background?: string;
}

export interface Track {
  id: string;
  title: string;
  artist_id: string;
  artist_name: string;
  album_id: string;
  album_title: string;
  duration_ms: number;
  artwork: TrackArtwork;
  audio: AudioSource;
  mood: TrackMood;
  genre: string;
  accent_theme: AccentTheme;
  playable_in_demo_mode: boolean;
}

export interface PaginatedTrackResponse {
  items: Track[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PlaybackPosition {
  position_ms: number;
}

export interface Volume {
  level: number;
}

export interface QueueItem {
  track_id: string;
  title: string;
  artist_name: string;
  duration_ms: number;
}

export interface ActiveTrack {
  track_id: string;
  title: string;
  artist_name: string;
  album_title: string;
  duration_ms: number;
  artwork: TrackArtwork;
  audio: AudioSource;
  mood: TrackMood;
  genre: string;
  accent_theme: AccentTheme;
  playable_in_demo_mode: boolean;
  position: PlaybackPosition;
}

export interface PlayerSession {
  state: PlaybackState;
  active_track: ActiveTrack | null;
  queue: QueueItem[];
  queue_index: number | null;
  volume: Volume;
  shuffle: boolean;
  repeat_mode: RepeatMode;
}

export interface PointsAwardExplanation {
  reason: string;
  melody_points: number;
  experience: number;
  explanation: string;
}

export interface ListeningEventRecord {
  id: number;
  idempotency_key: string;
  track_id: string;
  event_type: ListeningEventType;
  position_ms: number;
  occurred_at: string;
  awards: PointsAwardExplanation[];
  melody_points_earned: number;
  experience_earned: number;
  duplicate: boolean;
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: string;

  constructor(message: string, status: number, body: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export class NetworkError extends Error {
  constructor(message = "Unable to reach the MusicBloom API.") {
    super(message);
    this.name = "NetworkError";
  }
}

export type AudioAvailability = "available" | "unavailable" | "preview-only";
