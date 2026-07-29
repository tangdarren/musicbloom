import { PageCard } from "../components/PageCard";

export function DevGardenPage() {
  return (
    <PageCard
      eyebrow="Developer tools"
      title="Dev garden sandbox"
      lede="A lightweight staging area for garden layouts, decoration slots, and visual experiments without touching production player state."
    >
      <p className="muted">
        Use this route while iterating on art direction, spacing, and
        accessibility before wiring live progression data.
      </p>
    </PageCard>
  );
}
