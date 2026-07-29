import type { ActiveTrack } from "../../api/types";
import { getAudioAvailability } from "../../api/client";
import { formatTime } from "../../player/format";

interface NowPlayingProps {
  track: ActiveTrack | null;
  positionMs: number;
  audioError: string | null;
}

export function NowPlaying({ track, positionMs, audioError }: NowPlayingProps) {
  if (!track) {
    return (
      <section className="now-playing now-playing--empty" aria-live="polite">
        <div className="now-playing__artwork now-playing__artwork--empty">
          <span aria-hidden="true">✿</span>
        </div>
        <div>
          <p className="eyebrow">Now playing</p>
          <h2>Choose a demo track to begin</h2>
          <p className="muted">
            Select a playable track from the browser or queue. Audio starts only
            after you press play.
          </p>
        </div>
      </section>
    );
  }

  const availability = getAudioAvailability(track);

  return (
    <section
      className="now-playing"
      aria-live="polite"
      style={{
        ["--accent-primary" as string]: track.accent_theme.primary,
        ["--accent-secondary" as string]: track.accent_theme.secondary,
      }}
    >
      <div
        className="now-playing__artwork"
        aria-hidden="true"
        style={{
          background: `linear-gradient(145deg, ${track.accent_theme.primary}, ${track.accent_theme.secondary})`,
        }}
      >
        <span>{track.title.slice(0, 1)}</span>
      </div>
      <div className="now-playing__meta">
        <p className="eyebrow">Now playing</p>
        <h2>{track.title}</h2>
        <p className="now-playing__artist">
          {track.artist_name} · {track.album_title}
        </p>
        <div className="tag-row">
          <span className="tag">{track.mood}</span>
          <span className="tag">{track.genre}</span>
          {availability !== "available" ? (
            <span className="tag tag--warning">{availability}</span>
          ) : null}
        </div>
        <p className="muted">
          {formatTime(positionMs)} elapsed · {formatTime(track.duration_ms)}{" "}
          catalog duration
        </p>
        {audioError ? (
          <p className="player-alert" role="alert">
            {audioError}
          </p>
        ) : null}
      </div>
    </section>
  );
}
