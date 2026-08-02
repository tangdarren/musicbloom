import { resolveMediaPath } from "../../api/client";
import type { FavoriteTrackItem } from "../../api/types";
import { EmptyState } from "../EmptyState";
import { InlineAlert } from "../InlineAlert";
import { LoadingState } from "../LoadingState";
import { formatTime } from "../../player/format";
import { FavoriteToggleButton } from "./FavoriteToggleButton";

interface FavoritesPanelProps {
  favorites: FavoriteTrackItem[];
  isLoading: boolean;
  isError: boolean;
  isToggling: (trackId: string) => boolean;
  onToggleFavorite: (trackId: string) => void;
  onPlay: (trackId: string) => void;
  onQueue: (trackId: string) => void;
}

export function FavoritesPanel({
  favorites,
  isLoading,
  isError,
  isToggling,
  onToggleFavorite,
  onPlay,
  onQueue,
}: FavoritesPanelProps) {
  return (
    <section className="favorites-panel" aria-label="Favorite tracks">
      <div className="panel-heading">
        <h3>Favorites</h3>
        <span className="muted">
          {favorites.length} bloom{favorites.length === 1 ? "" : "s"}
        </span>
      </div>

      {isLoading ? <LoadingState label="Gathering favorite blooms" /> : null}

      {isError ? (
        <InlineAlert>
          Unable to load favorites. Please try again in a moment.
        </InlineAlert>
      ) : null}

      {!isLoading && !isError && favorites.length === 0 ? (
        <EmptyState>
          No favorites yet. Tap the flower beside a track in the browser to save
          it here.
        </EmptyState>
      ) : null}

      {!isLoading && !isError && favorites.length > 0 ? (
        <ul className="favorites-panel__list">
          {favorites.map((item) => {
            const artworkSrc = resolveMediaPath(item.artwork);

            return (
              <li key={item.id} className="favorites-panel__item">
                <div className="favorites-panel__artwork" aria-hidden="true">
                  {artworkSrc ? (
                    <img src={artworkSrc} alt="" />
                  ) : (
                    <span>{item.title.slice(0, 1)}</span>
                  )}
                </div>
                <div className="favorites-panel__meta">
                  <strong>{item.title}</strong>
                  <span className="muted">
                    {item.artist_name} · {formatTime(item.duration_ms)}
                  </span>
                </div>
                <div className="favorites-panel__actions">
                  <FavoriteToggleButton
                    trackTitle={item.title}
                    isFavorited
                    disabled={isToggling(item.track_id)}
                    onToggle={() => onToggleFavorite(item.track_id)}
                  />
                  <button
                    type="button"
                    aria-label={`Play ${item.title}`}
                    disabled={!item.playable_in_demo_mode}
                    onClick={() => onPlay(item.track_id)}
                  >
                    Play
                  </button>
                  <button
                    type="button"
                    aria-label={`Queue ${item.title}`}
                    disabled={!item.playable_in_demo_mode}
                    onClick={() => onQueue(item.track_id)}
                  >
                    Queue
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}
    </section>
  );
}
