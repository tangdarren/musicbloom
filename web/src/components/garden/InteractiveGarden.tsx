import { useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import {
  usePlaybackSignals,
  usePrefersReducedMotion,
} from "../../player/PlaybackSignalsContext";
import { PageIntro } from "../PageIntro";
import { BloomBud } from "./BloomBud";
import { moodLabel } from "./gardenMood";
import { DecorationPanel, GardenScene } from "./GardenScene";
import { useGardenEffects } from "./useGardenEffects";

const GARDEN_KEY = ["garden"] as const;
const DECORATIONS_KEY = ["decorations"] as const;

function StatCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <div className="garden-stat">
      <p className="garden-stat__label">{label}</p>
      <p className="garden-stat__value">{value}</p>
      {detail ? <p className="garden-stat__detail muted">{detail}</p> : null}
    </div>
  );
}

export function InteractiveGarden() {
  const queryClient = useQueryClient();
  const reducedMotion = usePrefersReducedMotion();
  const { isPlaying, isPaused } = usePlaybackSignals();
  const [busyId, setBusyId] = useState<string | null>(null);

  const gardenQuery = useQuery({
    queryKey: GARDEN_KEY,
    queryFn: () => apiClient.getGarden(),
    refetchInterval: 5000,
  });

  const decorationsQuery = useQuery({
    queryKey: DECORATIONS_KEY,
    queryFn: () => apiClient.getDecorations(),
  });

  const garden = gardenQuery.data;
  const { bloomingFlowerId, celebrating, streakEffect } = useGardenEffects(
    garden,
    reducedMotion,
  );

  const equipMutation = useMutation({
    mutationFn: (decorationId: string) => apiClient.equipDecoration(decorationId),
    onMutate: (decorationId) => setBusyId(decorationId),
    onSettled: async () => {
      setBusyId(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: GARDEN_KEY }),
        queryClient.invalidateQueries({ queryKey: DECORATIONS_KEY }),
      ]);
    },
  });

  const unequipMutation = useMutation({
    mutationFn: (decorationId: string) =>
      apiClient.unequipDecoration(decorationId),
    onMutate: (decorationId) => setBusyId(decorationId),
    onSettled: async () => {
      setBusyId(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: GARDEN_KEY }),
        queryClient.invalidateQueries({ queryKey: DECORATIONS_KEY }),
      ]);
    },
  });

  if (gardenQuery.isLoading) {
    return <p className="garden-loading">Growing your garden…</p>;
  }

  if (gardenQuery.isError || !garden) {
    return (
      <p className="garden-error" role="alert">
        We could not load your garden right now. Try refreshing the page.
      </p>
    );
  }

  const resting = isPaused || (!isPlaying && garden.tracks_completed > 0);
  const currentMood = moodLabel(garden.mood, resting && isPaused);

  return (
    <div className="garden-page__layout">
      <section className="garden-page__hero" aria-labelledby="garden-title">
        <PageIntro
          as="div"
          className="garden-page__intro"
          eyebrow={garden.profile.garden_name}
          title="Your MusicBloom garden"
          titleId="garden-title"
          lede="BloomBud watches over flowers for your favorite artists, milestone plants, and the decorations you unlock by listening."
        />

        <div className="garden-page__stats">
          <StatCard label="Level" value={garden.level.level} />
          <StatCard label="Melody Points" value={garden.melody_points} />
          <StatCard
            label="Streak"
            value={`${garden.streak.current_days} day${
              garden.streak.current_days === 1 ? "" : "s"
            }`}
          />
          <StatCard label="Garden mood" value={currentMood} />
        </div>
      </section>

      <div className="garden-page__main">
        <div className="garden-page__scene-wrap">
          <BloomBud
            resting={resting && isPaused}
            celebrating={celebrating}
            reducedMotion={reducedMotion}
          />
          <GardenScene
            flowers={garden.artist_flowers}
            plants={garden.milestone_plants}
            equipped={garden.equipped_decorations}
            swaying={isPlaying}
            bloomingFlowerId={bloomingFlowerId}
            streakEffect={streakEffect}
            reducedMotion={reducedMotion}
          />
        </div>

        <aside className="garden-page__sidebar">
          <section className="garden-panel">
            <h2>Decorations</h2>
            <p className="muted">
              Unlocked: {garden.unlocked_decorations.length} · Equipped:{" "}
              {garden.equipped_decorations.length}
            </p>
            <DecorationPanel
              decorations={decorationsQuery.data ?? []}
              busyId={busyId}
              onEquip={(id) => equipMutation.mutate(id)}
              onUnequip={(id) => unequipMutation.mutate(id)}
            />
          </section>

          <section className="garden-panel">
            <h2>Recent achievements</h2>
            {garden.recent_achievements.length === 0 ? (
              <p className="garden-panel__empty">
                Start listening to unlock your first achievement.
              </p>
            ) : (
              <ul className="garden-achievements">
                {garden.recent_achievements.map((achievement) => (
                  <li key={achievement.achievement_id}>
                    <strong>{achievement.title}</strong>
                    <span className="garden-achievements__status">
                      {achievement.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="garden-panel">
            <h2>Listening milestones</h2>
            <ul className="garden-milestones">
              {garden.milestone_plants.map((plant) => (
                <li key={plant.id}>
                  <strong>{plant.title}</strong>
                  <span>
                    {plant.progress}/{plant.target}
                    {plant.unlocked ? " · Grown" : ""}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}
