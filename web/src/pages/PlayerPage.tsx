import { PlayerProvider } from "../player/PlayerContext";
import { VisualPlayer } from "../components/player/VisualPlayer";

export function PlayerPage() {
  return (
    <section className="page player-page">
      <header className="player-page__header">
        <p className="eyebrow">Visual player</p>
        <h1>Garden playback studio</h1>
        <p className="lede">
          Play demo catalog tracks, manage your queue, and send listening events
          to the MusicBloom backend for Melody Points and quest progress.
        </p>
      </header>
      <PlayerProvider>
        <VisualPlayer />
      </PlayerProvider>
    </section>
  );
}
