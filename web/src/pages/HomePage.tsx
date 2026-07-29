import { Link } from "react-router-dom";

import { PageCard } from "../components/PageCard";

export function HomePage() {
  return (
    <PageCard
      eyebrow="Welcome to the meadow"
      title="Grow your music garden, one song at a time"
      lede="MusicBloom turns listening into a cozy garden adventure. Earn Melody Points, complete quests, unlock decorations, and keep BloomBud cheerful while you explore the demo catalog."
    >
      <div className="hero-grid">
        <div className="feature-list">
          <div className="feature-chip">
            <span aria-hidden="true">🌱</span>
            <div>
              <strong>Visual garden</strong>
              <p>Plants bloom as you listen and return each day.</p>
            </div>
          </div>
          <div className="feature-chip">
            <span aria-hidden="true">🎵</span>
            <div>
              <strong>Demo player</strong>
              <p>Play fictional tracks while the backend tracks progress.</p>
            </div>
          </div>
          <div className="feature-chip">
            <span aria-hidden="true">✨</span>
            <div>
              <strong>Quests & achievements</strong>
              <p>Daily goals and lifetime milestones with unlockable rewards.</p>
            </div>
          </div>
        </div>

        <div className="hero-actions">
          <Link to="/player" className="button button--primary">
            Open visual player
          </Link>
          <Link to="/garden" className="button button--secondary">
            Visit your garden
          </Link>
        </div>
      </div>
    </PageCard>
  );
}
