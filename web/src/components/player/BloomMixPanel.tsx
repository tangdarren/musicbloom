import { useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient, resolveMediaPath } from "../../api/client";
import type { Track, TrackMood } from "../../api/types";
import { generateBloomMix } from "../../player/bloomMix";
import { BLOOM_MIX_MOODS } from "../../player/bloomMixMoods";
import { formatTime } from "../../player/format";
import { LoadingState } from "../LoadingState";

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Unable to load BloomMix tracks.";
}

function MixPreviewItem({ track }: { track: Track }) {
  const artworkSrc = resolveMediaPath(track.artwork);
  const durationLabel =
    typeof track.duration_ms === "number" && track.duration_ms > 0
      ? formatTime(track.duration_ms)
      : null;

  return (
    <li className="bloom-mix__preview-item">
      <div
        className="bloom-mix__artwork"
        aria-hidden="true"
        style={
          artworkSrc
            ? undefined
            : {
                background: `linear-gradient(145deg, ${track.accent_theme.primary}, ${track.accent_theme.secondary})`,
              }
        }
      >
        {artworkSrc ? (
          <img src={artworkSrc} alt="" />
        ) : (
          <span>{track.title.slice(0, 1)}</span>
        )}
      </div>
      <div className="bloom-mix__preview-meta">
        <strong>{track.title}</strong>
        <span className="muted">
          {track.artist_name}
          {durationLabel ? ` · ${durationLabel}` : ""}
        </span>
      </div>
    </li>
  );
}

export function BloomMixPanel() {
  const [selectedMood, setSelectedMood] = useState<TrackMood | null>(null);
  const [seed, setSeed] = useState(1);

  const tracksQuery = useQuery({
    queryKey: ["tracks", "bloom-mix", selectedMood],
    queryFn: () =>
      apiClient.getTracks({
        mood: selectedMood ?? undefined,
        page: 1,
        page_size: 50,
      }),
    enabled: selectedMood !== null,
  });

  const mix = useMemo(() => {
    if (!selectedMood || !tracksQuery.data) {
      return [];
    }
    return generateBloomMix(tracksQuery.data.items, selectedMood, seed);
  }, [selectedMood, seed, tracksQuery.data]);

  const selectMood = (mood: TrackMood) => {
    setSelectedMood(mood);
    setSeed(1);
  };

  const refreshMix = () => {
    setSeed((current) => current + 1);
  };

  let resultContent: ReactNode;
  if (selectedMood === null) {
    resultContent = (
      <p className="muted">
        Choose a mood to grow a five-song BloomMix preview.
      </p>
    );
  } else if (tracksQuery.isLoading) {
    resultContent = <LoadingState label="Growing your BloomMix" />;
  } else if (tracksQuery.isError) {
    resultContent = (
      <div className="player-alert" role="alert">
        {getErrorMessage(tracksQuery.error)}
      </div>
    );
  } else if (mix.length === 0) {
    resultContent = (
      <p className="muted" role="status">
        No playable tracks are available for this mood right now.
      </p>
    );
  } else {
    resultContent = (
      <div className="bloom-mix__preview">
        <div className="panel-heading">
          <h4>Mix preview</h4>
          <span className="muted">
            {mix.length} track{mix.length === 1 ? "" : "s"}
          </span>
        </div>
        <ol className="bloom-mix__preview-list">
          {mix.map((track) => (
            <MixPreviewItem key={track.id} track={track} />
          ))}
        </ol>
        <button
          type="button"
          className="bloom-mix__refresh"
          onClick={refreshMix}
        >
          Refresh mix
        </button>
      </div>
    );
  }

  return (
    <section className="bloom-mix-panel" aria-label="BloomMix">
      <div className="panel-heading">
        <h3>BloomMix</h3>
        <span className="muted">Mood playlist preview</span>
      </div>

      <div
        className="bloom-mix__moods"
        role="group"
        aria-label="BloomMix moods"
      >
        {BLOOM_MIX_MOODS.map((mood) => {
          const isSelected = selectedMood === mood.id;
          return (
            <button
              key={mood.id}
              type="button"
              className={
                isSelected
                  ? "bloom-mix__mood is-selected"
                  : "bloom-mix__mood"
              }
              aria-pressed={isSelected}
              onClick={() => selectMood(mood.id)}
            >
              <span className="bloom-mix__mood-name">{mood.name}</span>
              <span className="bloom-mix__mood-description">
                {mood.description}
              </span>
            </button>
          );
        })}
      </div>

      <div className="bloom-mix__result" aria-live="polite">
        {resultContent}
      </div>
    </section>
  );
}
