import { Link } from "react-router-dom";

import { PageCard } from "../components/PageCard";

export function NotFoundPage() {
  return (
    <PageCard
      eyebrow="Lost in the clover"
      title="Page not found"
      lede="That path hasn't sprouted yet. Choose a destination below to keep exploring MusicBloom."
    >
      <Link to="/" className="button button--primary">
        Back to home
      </Link>
    </PageCard>
  );
}
