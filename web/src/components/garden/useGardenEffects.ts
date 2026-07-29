import { useEffect, useRef, useState } from "react";

import type { GardenState } from "../../api/gardenTypes";

const STREAK_MILESTONES = [3, 7];

export function useGardenEffects(
  garden: GardenState | undefined,
  reducedMotion: boolean,
) {
  const previousRef = useRef<{
    tracksCompleted: number;
    level: number;
    streakDays: number;
  } | null>(null);

  const [bloomingFlowerId, setBloomingFlowerId] = useState<string | null>(null);
  const [celebrating, setCelebrating] = useState(false);
  const [streakEffect, setStreakEffect] = useState(false);

  useEffect(() => {
    if (!garden) {
      return;
    }

    const snapshot = {
      tracksCompleted: garden.tracks_completed,
      level: garden.level.level,
      streakDays: garden.streak.current_days,
    };

    if (reducedMotion) {
      previousRef.current = snapshot;
      return;
    }

    const previous = previousRef.current;
    if (previous) {
      const timers: number[] = [];

      if (garden.tracks_completed > previous.tracksCompleted) {
        const newestFlower =
          garden.artist_flowers[garden.artist_flowers.length - 1];
        if (newestFlower) {
          timers.push(
            window.setTimeout(() => {
              setBloomingFlowerId(newestFlower.artist_id);
              timers.push(
                window.setTimeout(() => setBloomingFlowerId(null), 2400),
              );
            }, 0),
          );
        }
      }

      if (garden.level.level > previous.level) {
        timers.push(
          window.setTimeout(() => {
            setCelebrating(true);
            timers.push(
              window.setTimeout(() => setCelebrating(false), 3200),
            );
          }, 0),
        );
      }

      for (const milestone of STREAK_MILESTONES) {
        if (
          previous.streakDays < milestone &&
          garden.streak.current_days >= milestone
        ) {
          timers.push(
            window.setTimeout(() => {
              setStreakEffect(true);
              timers.push(
                window.setTimeout(() => setStreakEffect(false), 2800),
              );
            }, 0),
          );
          break;
        }
      }

      previousRef.current = snapshot;

      return () => {
        for (const timer of timers) {
          window.clearTimeout(timer);
        }
      };
    }

    previousRef.current = snapshot;
  }, [garden, reducedMotion]);

  return { bloomingFlowerId, celebrating, streakEffect };
}
