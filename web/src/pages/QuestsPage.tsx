import { PageCard } from "../components/PageCard";

export function QuestsPage() {
  return (
    <PageCard
      eyebrow="Daily & weekly goals"
      title="Quest board"
      lede="Quest progress is already tracked by the backend. This page will surface daily and weekly objectives with completion percentages and claim buttons."
    >
      <ul className="bullet-list">
        <li>Complete three tracks today</li>
        <li>Listen to three different artists</li>
        <li>Maintain a three-day streak this week</li>
      </ul>
    </PageCard>
  );
}
