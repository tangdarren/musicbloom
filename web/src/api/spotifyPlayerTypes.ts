export type SpotifyPlaybackStatus = "idle" | "playing" | "paused";

export interface SpotifyPlayerTrack {
  track_id: string;
  title: string;
  artist_name: string;
  album_title: string | null;
  duration_ms: number;
  artwork_url: string | null;
  spotify_uri: string | null;
}

export interface SpotifyPlayerDevice {
  id: string | null;
  name: string;
  type: string;
  is_active: boolean;
  volume_percent: number | null;
}

export interface SpotifyRecentTrack {
  track: SpotifyPlayerTrack;
  played_at: string;
}

export interface SpotifyPlayerSnapshot {
  status: SpotifyPlaybackStatus;
  configured: boolean;
  connected: boolean;
  is_playing: boolean;
  progress_ms: number | null;
  track: SpotifyPlayerTrack | null;
  device: SpotifyPlayerDevice | null;
  shuffle: boolean | null;
  repeat_mode: string | null;
  recently_played: SpotifyRecentTrack[];
  message: string | null;
  control_available: boolean;
  control_unavailable_reason: string | null;
}
