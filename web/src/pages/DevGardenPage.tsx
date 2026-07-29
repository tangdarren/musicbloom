import { PageCard } from "../components/PageCard";
import { DevGardenExperience } from "../components/dev-garden/DevGardenExperience";

export function DevGardenPage() {
  return (
    <PageCard
      eyebrow="Portfolio tools"
      title="Dev Garden"
      lede="A separate cutesy scene that turns Azure Pipelines build health into something BloomBud can nurture. This garden is independent from your listening garden."
    >
      <p className="muted">
        MusicBloom reads normalized pipeline metadata from the backend only.
        Azure DevOps credentials never reach the browser.
      </p>
      <DevGardenExperience />
    </PageCard>
  );
}
