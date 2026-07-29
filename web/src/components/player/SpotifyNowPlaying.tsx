import type { SpotifyPlayerSnapshot } from "../../api/spotifyPlayerTypes";
import { formatTime } from "../../player/format";

interface SpotifyNowPlayingProps {
  snapshot: SpotifyPlayerSnapshot;
  positionMs: number;
  errorMessage: string | null;
}

export function SpotifyNowPlaying({
  snapshot,
  positionMs,
  errorMessage,
}: SpotifyNowPlayingProps) {
  const track = snapshot.track;

  if (!track) {
    return (
      <section className="now-playing now-playing--empty" aria-live="polite">
        <div className="now-playing__artwork now-playing__artwork--empty">
          <span aria-hidden="true">♫</span>
        </div>
        <div>
          <p className="eyebrow">Spotify playback</p>
          <h2>No active Spotify playback</h2>
          <p className="muted">
            {snapshot.message ??
              "Start playing on a Spotify device to see live metadata here."}
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="now-playing" aria-live="polite">
      <div className="now-playing__meta">
        <p className="eyebrow">Spotify now playing</p>
        <h2>{track.title}</h2>
        <p className="now-playing__artist">
          {track.artist_name}
          {track.album_title ? ` · ${track.album_title}` : ""}
        </p>
        <p className="muted">
          {formatTime(positionMs)} elapsed · {formatTime(track.duration_ms)} track
          duration
        </p>
        {snapshot.device ? (
          <p className="muted">
            Active device: {snapshot.device.name} ({snapshot.device.type})
          </p>
        ) : null}
        {snapshot.control_unavailable_reason ? (
          <p className="player-alert" role="status">
            {snapshot.control_unavailable_reason}
          </p>
        ) : null}
        {errorMessage ? (
          <p className="player-alert" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </div>
    </section>
  );
}
