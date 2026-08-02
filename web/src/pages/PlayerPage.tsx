import { PageFrame } from "../components/PageFrame";
import { PageIntro } from "../components/PageIntro";
import { PlaybackStudio } from "../components/player/PlaybackStudio";
import { PlaybackModeProvider } from "../player/PlaybackModeContext";
import { PlayerProvider } from "../player/PlayerContext";

export function PlayerPage() {
  return (
    <PageFrame className="player-page">
      <PageIntro
        as="header"
        className="player-page__header"
        eyebrow="Visual player"
        title="Garden playback studio"
        lede="Choose Demo Mode for the fictional catalog or Spotify Mode for live metadata and playback control through your connected account."
      />
      <PlaybackModeProvider>
        <PlayerProvider>
          <PlaybackStudio />
        </PlayerProvider>
      </PlaybackModeProvider>
    </PageFrame>
  );
}
