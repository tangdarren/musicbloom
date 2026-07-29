import type { RepeatMode } from "../../api/types";

interface PlayerControlsProps {
  isPlaying: boolean;
  shuffle: boolean;
  repeatMode: RepeatMode;
  disabled?: boolean;
  onTogglePlayPause: () => void;
  onPrevious: () => void;
  onNext: () => void;
  onToggleShuffle: () => void;
  onCycleRepeat: () => void;
}

const REPEAT_LABELS: Record<RepeatMode, string> = {
  off: "Repeat off",
  one: "Repeat one",
  all: "Repeat all",
};

export function PlayerControls({
  isPlaying,
  shuffle,
  repeatMode,
  disabled = false,
  onTogglePlayPause,
  onPrevious,
  onNext,
  onToggleShuffle,
  onCycleRepeat,
}: PlayerControlsProps) {
  return (
    <div className="player-controls" role="group" aria-label="Playback controls">
      <button
        type="button"
        className={`player-controls__chip ${shuffle ? "is-active" : ""}`}
        aria-pressed={shuffle}
        aria-label={shuffle ? "Disable shuffle" : "Enable shuffle"}
        disabled={disabled}
        onClick={onToggleShuffle}
      >
        Shuffle
      </button>
      <button
        type="button"
        className="player-controls__transport"
        aria-label="Previous track"
        disabled={disabled}
        onClick={onPrevious}
      >
        ‹
      </button>
      <button
        type="button"
        className="player-controls__play"
        aria-label={isPlaying ? "Pause playback" : "Start playback"}
        disabled={disabled}
        onClick={onTogglePlayPause}
      >
        {isPlaying ? "Pause" : "Play"}
      </button>
      <button
        type="button"
        className="player-controls__transport"
        aria-label="Next track"
        disabled={disabled}
        onClick={onNext}
      >
        ›
      </button>
      <button
        type="button"
        className={`player-controls__chip ${repeatMode !== "off" ? "is-active" : ""}`}
        aria-pressed={repeatMode !== "off"}
        aria-label={REPEAT_LABELS[repeatMode]}
        disabled={disabled}
        onClick={onCycleRepeat}
      >
        {repeatMode === "one" ? "Repeat 1" : "Repeat"}
      </button>
    </div>
  );
}
