import { PageCard } from "../components/PageCard";

export function GardenPage() {
  return (
    <PageCard
      eyebrow="Your meadow"
      title="Garden preview"
      lede="Decorations, plants, and BloomBud will live here. Listening sessions from the backend will eventually drive growth animations and placement tools."
    >
      <div className="garden-preview" aria-hidden="true">
        <span className="garden-preview__plot garden-preview__plot--north" />
        <span className="garden-preview__plot garden-preview__plot--center" />
        <span className="garden-preview__plot garden-preview__plot--south" />
      </div>
    </PageCard>
  );
}
