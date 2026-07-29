import type { SpotifyConnectionStatus, SpotifyPanelState } from "../../api/spotifyTypes";

interface SpotifyConnectionPanelProps {
  status: SpotifyConnectionStatus | undefined;
  panelState: SpotifyPanelState;
  isLoading: boolean;
  isDisconnecting: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

function statusCopy(
  panelState: SpotifyPanelState,
  status: SpotifyConnectionStatus | undefined,
): { title: string; description: string } {
  switch (panelState) {
    case "connecting":
      return {
        title: "Connecting to Spotify",
        description: "Redirecting you to Spotify to approve access.",
      };
    case "connected":
      return {
        title: "Spotify connected",
        description: status?.display_name
          ? `${status.display_name} is linked to MusicBloom.`
          : "Your Spotify account is linked to MusicBloom.",
      };
    case "error":
      return {
        title: "Spotify connection needs attention",
        description:
          status?.error_message ??
          "We could not refresh your Spotify session. Disconnect and try again.",
      };
    default:
      if (status?.configured === false) {
        return {
          title: "Spotify optional",
          description:
            "Demo mode works without Spotify credentials. Add server-side Spotify OAuth settings to enable account linking.",
        };
      }
      return {
        title: "Connect Spotify",
        description:
          "Link your Spotify account when credentials are configured. Playback controls are coming later.",
      };
  }
}

export function SpotifyConnectionPanel({
  status,
  panelState,
  isLoading,
  isDisconnecting,
  onConnect,
  onDisconnect,
}: SpotifyConnectionPanelProps) {
  const copy = statusCopy(panelState, status);
  const canConnect =
    status?.configured !== false &&
    panelState !== "connected" &&
    panelState !== "connecting";
  const canDisconnect = panelState === "connected" || panelState === "error";

  return (
    <section className="spotify-panel" aria-labelledby="spotify-panel-title">
      <div className="spotify-panel__header">
        <p className="eyebrow">Account linking</p>
        <h2 id="spotify-panel-title">{copy.title}</h2>
        <p className="lede">{copy.description}</p>
      </div>

      <div className="spotify-panel__status" data-state={panelState}>
        <span className="spotify-panel__badge">{panelState}</span>
        {isLoading ? <p className="muted">Checking connection status…</p> : null}
        {status?.configured === false ? (
          <p className="muted">
            Spotify OAuth is not configured on the server. Demo mode remains fully
            available.
          </p>
        ) : null}
        {status?.spotify_user_id ? (
          <p className="muted">Spotify user ID: {status.spotify_user_id}</p>
        ) : null}
        {status?.scopes.length ? (
          <p className="muted">Scopes: {status.scopes.join(", ")}</p>
        ) : null}
      </div>

      <div className="spotify-panel__actions">
        {canConnect ? (
          <button
            type="button"
            className="button button--primary"
            onClick={onConnect}
          >
            Connect Spotify
          </button>
        ) : null}
        {canDisconnect ? (
          <button
            type="button"
            className="button button--secondary"
            onClick={onDisconnect}
            disabled={isDisconnecting}
          >
            {isDisconnecting ? "Disconnecting…" : "Disconnect Spotify"}
          </button>
        ) : null}
      </div>
    </section>
  );
}
