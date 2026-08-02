import type { Track } from "../../api/types";
import { getAudioAvailability } from "../../api/client";
import { formatTime } from "../../player/format";
import { FavoriteToggleButton } from "./FavoriteToggleButton";

interface TrackBrowserProps {
  tracks: Track[];
  activeTrackId: string | null;
  favoritedTrackIds: ReadonlySet<string>;
  isFavoritePending?: (trackId: string) => boolean;
  onPlay: (trackId: string) => void;
  onQueue: (trackId: string) => void;
  onToggleFavorite: (trackId: string) => void;
}

export function TrackBrowser({
  tracks,
  activeTrackId,
  favoritedTrackIds,
  isFavoritePending,
  onPlay,
  onQueue,
  onToggleFavorite,
}: TrackBrowserProps) {
  return (
    <section className="track-browser" aria-label="Demo track browser">
      <div className="panel-heading">
        <h3>Track browser</h3>
        <span className="muted">{tracks.length} demo tracks</span>
      </div>
      <ul className="track-browser__list">
        {tracks.map((track) => {
          const availability = getAudioAvailability(track);
          const isActive = track.id === activeTrackId;
          const isFavorited = favoritedTrackIds.has(track.id);

          return (
            <li
              key={track.id}
              className={isActive ? "track-browser__item is-active" : "track-browser__item"}
              style={{
                ["--accent-primary" as string]: track.accent_theme.primary,
              }}
            >
              <div className="track-browser__meta">
                <strong>{track.title}</strong>
                <span className="muted">
                  {track.artist_name} · {formatTime(track.duration_ms)}
                </span>
                <div className="tag-row">
                  <span className="tag">{track.mood}</span>
                  <span className="tag">{track.genre}</span>
                  {availability !== "available" ? (
                    <span className="tag tag--warning">{availability}</span>
                  ) : null}
                </div>
              </div>
              <div className="track-browser__actions">
                <FavoriteToggleButton
                  trackTitle={track.title}
                  isFavorited={isFavorited}
                  disabled={isFavoritePending?.(track.id) ?? false}
                  onToggle={() => onToggleFavorite(track.id)}
                />
                <button
                  type="button"
                  aria-label={`Play ${track.title}`}
                  disabled={!track.playable_in_demo_mode}
                  onClick={() => onPlay(track.id)}
                >
                  Play
                </button>
                <button
                  type="button"
                  aria-label={`Queue ${track.title}`}
                  disabled={!track.playable_in_demo_mode}
                  onClick={() => onQueue(track.id)}
                >
                  Queue
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
