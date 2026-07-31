import { useMemo, useRef, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, resolveMediaPath } from "../../api/client";
import { ApiError, NetworkError, type Track, type TrackMood } from "../../api/types";
import { useReducedMotion } from "../dev-garden/useReducedMotion";
import { generateBloomMix } from "../../player/bloomMix";
import { BLOOM_MIX_MOODS } from "../../player/bloomMixMoods";
import { formatTime } from "../../player/format";
import { planBloomMixPlant } from "../../player/plantBloomMix";
import { PLAYER_SESSION_KEY } from "../../player/PlayerContext";
import { usePlayer } from "../../player/usePlayer";

type PlantFeedback =
  | { kind: "success"; message: string }
  | { kind: "info"; message: string }
  | { kind: "partial"; message: string }
  | { kind: "error"; message: string };

function getBloomMixErrorMessage(
  error: unknown,
  context: "load" | "plant",
): string {
  if (error instanceof NetworkError) {
    return context === "load"
      ? "We couldn't reach MusicBloom to grow this mix. Check your connection and try again."
      : "We couldn't reach MusicBloom to plant this mix. Check your connection and try again.";
  }

  if (error instanceof ApiError) {
    if (error.status >= 500) {
      return "MusicBloom had trouble with that request. Please try again in a moment.";
    }
    if (error.status === 409) {
      return "Some of these tracks are already in your queue.";
    }
  }

  return context === "load"
    ? "We couldn't load tracks for this mood. Please try another mood or try again."
    : "We couldn't plant the mix into your queue. Please try again.";
}

function plantedCountLabel(count: number): string {
  return `${count} track${count === 1 ? "" : "s"}`;
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
        <strong className="bloom-mix__track-title">{track.title}</strong>
        <span className="bloom-mix__track-subtitle muted">
          <span className="bloom-mix__track-artist">{track.artist_name}</span>
          {durationLabel ? (
            <span className="bloom-mix__track-duration"> · {durationLabel}</span>
          ) : null}
        </span>
      </div>
    </li>
  );
}

function PlantCelebration() {
  return (
    <div className="bloom-mix__celebration" aria-hidden="true">
      <span className="bloom-mix__sprout" />
      <span className="bloom-mix__petal bloom-mix__petal--1" />
      <span className="bloom-mix__petal bloom-mix__petal--2" />
      <span className="bloom-mix__petal bloom-mix__petal--3" />
      <span className="bloom-mix__petal bloom-mix__petal--4" />
      <span className="bloom-mix__petal bloom-mix__petal--5" />
    </div>
  );
}

export function BloomMixPanel() {
  const queryClient = useQueryClient();
  const reducedMotion = useReducedMotion();
  const { session, playTrack, enqueueTrack } = usePlayer();
  const [selectedMood, setSelectedMood] = useState<TrackMood | null>(null);
  const [seed, setSeed] = useState(1);
  const [isPlanting, setIsPlanting] = useState(false);
  const [plantFeedback, setPlantFeedback] = useState<PlantFeedback | null>(
    null,
  );
  const plantingLockRef = useRef(false);

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

  const isMoodResultReady =
    selectedMood !== null &&
    tracksQuery.isSuccess &&
    !tracksQuery.isPending &&
    Boolean(tracksQuery.data);

  const isMoodLoading =
    selectedMood !== null &&
    (tracksQuery.isPending ||
      (tracksQuery.isFetching && !tracksQuery.isSuccess));

  const mix = useMemo(() => {
    if (!isMoodResultReady || !selectedMood || !tracksQuery.data) {
      return [];
    }
    return generateBloomMix(tracksQuery.data.items, selectedMood, seed);
  }, [isMoodResultReady, selectedMood, seed, tracksQuery.data]);

  const selectMood = (mood: TrackMood) => {
    if (isPlanting) {
      return;
    }
    setSelectedMood(mood);
    setSeed(1);
    setPlantFeedback(null);
  };

  const refreshMix = () => {
    if (isPlanting) {
      return;
    }
    setSeed((current) => current + 1);
    setPlantFeedback(null);
  };

  const plantThisMix = async () => {
    if (plantingLockRef.current || isPlanting || mix.length === 0 || !session) {
      return;
    }

    plantingLockRef.current = true;
    setIsPlanting(true);
    setPlantFeedback(null);

    const plan = planBloomMixPlant(
      mix.map((track) => track.id),
      session.active_track?.track_id ?? null,
      session.queue.map((item) => item.track_id),
    );

    if (plan.toPlant.length === 0) {
      setPlantFeedback({
        kind: "info",
        message: "Every track in this mix is already active or queued.",
      });
      setIsPlanting(false);
      plantingLockRef.current = false;
      return;
    }

    let planted = 0;

    try {
      if (plan.startWithPlay) {
        const [firstId, ...restIds] = plan.toPlant;
        await playTrack(firstId!);
        planted += 1;
        for (const trackId of restIds) {
          await enqueueTrack(trackId);
          planted += 1;
        }
      } else {
        for (const trackId of plan.toPlant) {
          await enqueueTrack(trackId);
          planted += 1;
        }
      }

      setPlantFeedback({
        kind: "success",
        message: `Planted ${plantedCountLabel(planted)} into your garden queue.`,
      });
    } catch (error) {
      if (planted > 0) {
        setPlantFeedback({
          kind: "partial",
          message: `Added ${plantedCountLabel(planted)}, but the rest of the mix could not be planted. ${getBloomMixErrorMessage(error, "plant")}`,
        });
      } else {
        setPlantFeedback({
          kind: "error",
          message: getBloomMixErrorMessage(error, "plant"),
        });
      }
    } finally {
      await queryClient.invalidateQueries({ queryKey: PLAYER_SESSION_KEY });
      setIsPlanting(false);
      plantingLockRef.current = false;
    }
  };

  let resultContent: ReactNode;
  if (selectedMood === null) {
    resultContent = (
      <p className="muted">
        Choose a mood to grow a five-song BloomMix preview.
      </p>
    );
  } else if (isMoodLoading) {
    resultContent = (
      <div className="loading-state" role="status">
        <span className="loading-state__spinner" aria-hidden="true" />
        <span>Growing your BloomMix</span>
      </div>
    );
  } else if (tracksQuery.isError) {
    resultContent = (
      <div className="player-alert" role="alert">
        <span className="bloom-mix__feedback-prefix">Unable to load</span>
        {getBloomMixErrorMessage(tracksQuery.error, "load")}
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
        <ol className="bloom-mix__preview-list" aria-label="BloomMix preview">
          {mix.map((track) => (
            <MixPreviewItem key={`${selectedMood}-${seed}-${track.id}`} track={track} />
          ))}
        </ol>
        <div className="bloom-mix__actions">
          <button
            type="button"
            className="bloom-mix__plant"
            disabled={isPlanting || !session}
            onClick={() => {
              void plantThisMix();
            }}
          >
            {isPlanting ? "Planting mix…" : "Plant this mix"}
          </button>
          <button
            type="button"
            className="bloom-mix__refresh"
            disabled={isPlanting}
            onClick={refreshMix}
          >
            Refresh mix
          </button>
        </div>
      </div>
    );
  }

  return (
    <section
      className={
        reducedMotion
          ? "bloom-mix-panel bloom-mix-panel--reduced-motion"
          : "bloom-mix-panel"
      }
      aria-label="BloomMix"
    >
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
              disabled={isPlanting}
              onClick={() => selectMood(mood.id)}
            >
              <span className="bloom-mix__mood-heading">
                <span className="bloom-mix__mood-name">{mood.name}</span>
                {isSelected ? (
                  <span className="bloom-mix__mood-selected-tag">Selected</span>
                ) : null}
              </span>
              <span className="bloom-mix__mood-description">
                {mood.description}
              </span>
            </button>
          );
        })}
      </div>

      <div
        className="bloom-mix__result"
        aria-live="polite"
        aria-atomic="true"
      >
        {resultContent}
        {plantFeedback ? (
          <div
            className={
              plantFeedback.kind === "error" || plantFeedback.kind === "partial"
                ? "player-alert bloom-mix__feedback"
                : plantFeedback.kind === "success"
                  ? "award-toast bloom-mix__feedback bloom-mix__feedback--success"
                  : "bloom-mix__feedback bloom-mix__feedback--info"
            }
            role={
              plantFeedback.kind === "error" || plantFeedback.kind === "partial"
                ? "alert"
                : "status"
            }
          >
            {plantFeedback.kind === "success" ? <PlantCelebration /> : null}
            <p>
              <span className="bloom-mix__feedback-prefix">
                {plantFeedback.kind === "success"
                  ? "Success: "
                  : plantFeedback.kind === "info"
                    ? "Note: "
                    : plantFeedback.kind === "partial"
                      ? "Partial: "
                      : "Error: "}
              </span>
              {plantFeedback.message}
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
