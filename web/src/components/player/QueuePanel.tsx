import type { QueueItem } from "../../api/types";
import { formatTime } from "../../player/format";

interface QueuePanelProps {
  queue: QueueItem[];
  activeTrackId: string | null;
  onRemove: (trackId: string) => void;
}

export function QueuePanel({
  queue,
  activeTrackId,
  onRemove,
}: QueuePanelProps) {
  return (
    <section className="queue-panel" aria-label="Playback queue">
      <div className="panel-heading">
        <h3>Queue</h3>
        <span className="muted">{queue.length} tracks</span>
      </div>
      {queue.length === 0 ? (
        <p className="muted">Queue a few demo tracks to plan your garden session.</p>
      ) : (
        <ol className="queue-list">
          {queue.map((item) => (
            <li
              key={`${item.track_id}-${item.title}`}
              className={
                item.track_id === activeTrackId ? "queue-list__item is-active" : "queue-list__item"
              }
            >
              <div>
                <strong>{item.title}</strong>
                <span className="muted">
                  {item.artist_name} · {formatTime(item.duration_ms)}
                </span>
              </div>
              <button
                type="button"
                aria-label={`Remove ${item.title} from queue`}
                onClick={() => onRemove(item.track_id)}
              >
                Remove
              </button>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
