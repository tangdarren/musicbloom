interface MetadataVisualizerProps {
  isPlaying: boolean;
  accentColor: string;
  artworkUrl: string | null;
  title: string;
}

export function MetadataVisualizer({
  isPlaying,
  accentColor,
  artworkUrl,
  title,
}: MetadataVisualizerProps) {
  return (
    <div
      className={`metadata-visualizer ${isPlaying ? "is-playing" : ""}`}
      aria-hidden="true"
      style={{ ["--accent-primary" as string]: accentColor }}
    >
      {artworkUrl ? (
        <img
          className="metadata-visualizer__artwork"
          src={artworkUrl}
          alt=""
        />
      ) : (
        <div className="metadata-visualizer__fallback">{title.slice(0, 1)}</div>
      )}
      <div className="metadata-visualizer__pulse" />
    </div>
  );
}
