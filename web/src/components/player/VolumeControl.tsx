interface VolumeControlProps {
  level: number;
  onChange: (level: number) => void;
}

export function VolumeControl({ level, onChange }: VolumeControlProps) {
  return (
    <div className="volume-control">
      <label htmlFor="volume-control">Volume</label>
      <input
        id="volume-control"
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={level}
        aria-valuetext={`${Math.round(level * 100)} percent`}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  );
}
