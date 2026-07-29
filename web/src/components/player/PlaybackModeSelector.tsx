import type { PlaybackMode } from "../../player/PlaybackModeContext";

interface PlaybackModeSelectorProps {
  mode: PlaybackMode;
  spotifyConnected: boolean;
  spotifyConfigured: boolean;
  onChange: (mode: PlaybackMode) => void;
}

export function PlaybackModeSelector({
  mode,
  spotifyConnected,
  spotifyConfigured,
  onChange,
}: PlaybackModeSelectorProps) {
  return (
    <div className="playback-mode-selector" role="group" aria-label="Playback mode">
      <button
        type="button"
        className={`playback-mode-selector__option ${
          mode === "demo" ? "is-active" : ""
        }`}
        aria-pressed={mode === "demo"}
        onClick={() => onChange("demo")}
      >
        Demo Mode
      </button>
      <button
        type="button"
        className={`playback-mode-selector__option ${
          mode === "spotify" ? "is-active" : ""
        }`}
        aria-pressed={mode === "spotify"}
        disabled={!spotifyConnected}
        onClick={() => onChange("spotify")}
      >
        Spotify Mode
      </button>
      {!spotifyConfigured ? (
        <p className="muted playback-mode-selector__hint">
          Spotify OAuth is not configured on the server. Demo mode remains fully
          available.
        </p>
      ) : null}
      {spotifyConfigured && !spotifyConnected ? (
        <p className="muted playback-mode-selector__hint">
          Connect your Spotify account on the home page before switching to
          Spotify Mode.
        </p>
      ) : null}
    </div>
  );
}
