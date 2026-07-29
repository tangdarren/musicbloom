/** Spotify connection API types. */

export type SpotifyConnectionStatusCode = "disconnected" | "connected" | "error";

export interface SpotifyConnectionStatus {
  status: SpotifyConnectionStatusCode;
  configured: boolean;
  display_name: string | null;
  spotify_user_id: string | null;
  scopes: string[];
  expires_at: string | null;
  error_code: string | null;
  error_message: string | null;
}

export interface SpotifyDisconnectResult {
  disconnected: boolean;
}

export type SpotifyPanelState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";
