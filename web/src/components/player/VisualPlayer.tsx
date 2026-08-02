import { InlineAlert } from "../InlineAlert";
import { LoadingState } from "../LoadingState";
import { useFavorites } from "../../player/useFavorites";
import { usePlayer } from "../../player/usePlayer";
import { AudioVisualizer } from "./AudioVisualizer";
import { BloomMixPanel } from "./BloomMixPanel";
import { DemoModeBanner } from "./DemoModeBanner";
import { FavoritesPanel } from "./FavoritesPanel";
import { NowPlaying } from "./NowPlaying";
import { PlayerControls } from "./PlayerControls";
import { QueuePanel } from "./QueuePanel";
import { SeekBar } from "./SeekBar";
import { TrackBrowser } from "./TrackBrowser";
import { VolumeControl } from "./VolumeControl";

export function VisualPlayer() {
  const {
    session,
    tracks,
    isLoading,
    isError,
    errorMessage,
    localPositionMs,
    audioAvailable,
    audioError,
    recentAwards,
    playTrack,
    togglePlayPause,
    seekTo,
    changeVolume,
    toggleShuffle,
    cycleRepeat,
    skipNext,
    skipPrevious,
    enqueueTrack,
    removeQueuedTrack,
    analyser,
    isPlaying,
    activeTrack,
  } = usePlayer();
  const {
    favorites,
    favoritedTrackIds,
    isLoading: favoritesLoading,
    isError: favoritesError,
    toggleFavorite,
    isToggling,
  } = useFavorites();

  if (isLoading) {
    return <LoadingState label="Loading visual player" />;
  }

  if (isError || !session) {
    return (
      <InlineAlert>
        {errorMessage ?? "Unable to load the player session."}
      </InlineAlert>
    );
  }

  const durationMs = activeTrack?.duration_ms ?? 0;
  const accent = activeTrack?.accent_theme.primary ?? "#5fae79";

  return (
    <div className="visual-player">
      <DemoModeBanner />

      <div className="visual-player__layout">
        <div className="visual-player__main card">
          <NowPlaying
            track={activeTrack}
            positionMs={localPositionMs}
            audioError={audioError}
          />

          <AudioVisualizer
            analyser={analyser}
            isPlaying={isPlaying && audioAvailable}
            accentColor={accent}
          />

          <SeekBar
            positionMs={localPositionMs}
            durationMs={durationMs}
            disabled={!activeTrack}
            onSeek={(positionMs) => {
              void seekTo(positionMs);
            }}
          />

          <PlayerControls
            isPlaying={isPlaying}
            shuffle={session.shuffle}
            repeatMode={session.repeat_mode}
            disabled={!activeTrack && session.queue.length === 0}
            onTogglePlayPause={() => {
              void togglePlayPause();
            }}
            onPrevious={() => {
              void skipPrevious();
            }}
            onNext={() => {
              void skipNext();
            }}
            onToggleShuffle={() => {
              void toggleShuffle();
            }}
            onCycleRepeat={() => {
              void cycleRepeat();
            }}
          />

          <VolumeControl
            level={session.volume.level}
            onChange={(level) => {
              void changeVolume(level);
            }}
          />

          {recentAwards.length > 0 ? (
            <div className="award-toast" role="status" aria-live="polite">
              {recentAwards.map((award) => (
                <p key={award}>{award}</p>
              ))}
            </div>
          ) : null}
        </div>

        <div className="visual-player__side">
          <BloomMixPanel />
          <FavoritesPanel
            favorites={favorites}
            isLoading={favoritesLoading}
            isError={favoritesError}
            isToggling={isToggling}
            onToggleFavorite={toggleFavorite}
            onPlay={(trackId) => {
              void playTrack(trackId);
            }}
            onQueue={(trackId) => {
              void enqueueTrack(trackId);
            }}
          />
          <QueuePanel
            queue={session.queue}
            activeTrackId={activeTrack?.track_id ?? null}
            onRemove={(trackId) => {
              void removeQueuedTrack(trackId);
            }}
          />
          <TrackBrowser
            tracks={tracks}
            activeTrackId={activeTrack?.track_id ?? null}
            favoritedTrackIds={favoritedTrackIds}
            isFavoritePending={isToggling}
            onPlay={(trackId) => {
              void playTrack(trackId);
            }}
            onQueue={(trackId) => {
              void enqueueTrack(trackId);
            }}
            onToggleFavorite={toggleFavorite}
          />
        </div>
      </div>
    </div>
  );
}
