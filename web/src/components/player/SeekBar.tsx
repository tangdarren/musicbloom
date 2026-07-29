import { formatTime } from "../../player/format";

interface SeekBarProps {
  positionMs: number;
  durationMs: number;
  disabled?: boolean;
  onSeek: (positionMs: number) => void;
}

export function SeekBar({
  positionMs,
  durationMs,
  disabled = false,
  onSeek,
}: SeekBarProps) {
  const safeDuration = Math.max(durationMs, 1);
  const percentage = (positionMs / safeDuration) * 100;

  return (
    <div className="seek-bar">
      <label className="visually-hidden" htmlFor="seek-bar">
        Seek playback position
      </label>
      <input
        id="seek-bar"
        type="range"
        min={0}
        max={safeDuration}
        step={1000}
        value={positionMs}
        disabled={disabled}
        aria-valuetext={`${formatTime(positionMs)} of ${formatTime(durationMs)}`}
        onChange={(event) => onSeek(Number(event.target.value))}
        className="seek-bar__input"
      />
      <div className="seek-bar__track" aria-hidden="true">
        <span
          className="seek-bar__progress"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="seek-bar__times">
        <span>{formatTime(positionMs)}</span>
        <span>{formatTime(durationMs)}</span>
      </div>
    </div>
  );
}
