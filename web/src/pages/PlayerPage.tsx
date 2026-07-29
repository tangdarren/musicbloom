import { PlayerProvider } from "../player/PlayerContext";
import { PlaybackModeProvider } from "../player/PlaybackModeContext";
import { PlaybackStudio } from "../components/player/PlaybackStudio";

export function PlayerPage() {
  return (
    <section className="page player-page">
      <header className="player-page__header">
        <p className="eyebrow">Visual player</p>
        <h1>Garden playback studio</h1>
        <p className="lede">
          Choose Demo Mode for the fictional catalog or Spotify Mode for live
          metadata and playback control through your connected account.
        </p>
      </header>
      <PlaybackModeProvider>
        <PlayerProvider>
          <PlaybackStudio />
        </PlayerProvider>
      </PlaybackModeProvider>
    </section>
  );
}
