import { PageCard } from "../components/PageCard";

export function AchievementsPage() {
  return (
    <PageCard
      eyebrow="Lifetime milestones"
      title="Achievement gallery"
      lede="Achievements like First Bloom and Level Up Listener are persisted server-side. This gallery will show locked, active, completed, and claimed states."
    >
      <ul className="bullet-list">
        <li>Reach MusicBloom level 2</li>
        <li>Complete your first track</li>
      </ul>
    </PageCard>
  );
}
