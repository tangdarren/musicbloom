import { InteractiveGarden } from "../components/garden/InteractiveGarden";
import { PageFrame } from "../components/PageFrame";

export function GardenPage() {
  return (
    <PageFrame className="garden-page">
      <InteractiveGarden />
    </PageFrame>
  );
}
