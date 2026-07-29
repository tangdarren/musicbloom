import { PageCard } from "../components/PageCard";

export function PlayerPage() {
  return (
    <PageCard
      eyebrow="Visual player"
      title="Player coming soon"
      lede="This route will host the full garden-themed playback experience. For now, explore the demo catalog through the FastAPI backend while the interface takes shape."
    >
      <p className="muted">
        Planned features: cozy playback controls, track artwork, queue
        management, and BloomBud reactions tied to listening events.
      </p>
    </PageCard>
  );
}
