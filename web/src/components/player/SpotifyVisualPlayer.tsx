import { useState } from "react";

import { LoadingState } from "../LoadingState";
import { MetadataVisualizer } from "./MetadataVisualizer";
import { PlayerControls } from "./PlayerControls";
import { SeekBar } from "./SeekBar";
import { SpotifyModeBanner } from "./SpotifyModeBanner";
import { SpotifyNowPlaying } from "./SpotifyNowPlaying";
import { VolumeControl } from "./VolumeControl";
import { useSpotifyPlayer } from "../spotify/useSpotifyPlayer";
import { clamp } from "../../player/format";

export function SpotifyVisualPlayer() {
  const {
    snapshot,
    isLoading,
    isError,
    errorMessage,
    controlError,
    isControlling,
    play,
    pause,
    next,
    previous,
    seek,
    setVolume,
  } = useSpotifyPlayer();

  const [seekOverride, setSeekOverride] = useState<number | null>(null);

  if (isLoading) {
    return <LoadingState label="Loading Spotify playback" />;
  }

  if (isError || !snapshot) {
    return (
      <div className="player-alert" role="alert">
        {errorMessage ?? "Unable to load Spotify playback metadata."}
      </div>
    );
  }

  const track = snapshot.track;
  const serverPositionMs = snapshot.progress_ms ?? 0;
  const localPositionMs = seekOverride ?? serverPositionMs;
  const durationMs = track?.duration_ms ?? 0;
  const isPlaying = snapshot.status === "playing";
  const controlsDisabled =
    isControlling || !snapshot.control_available || !snapshot.connected;
  const volumeLevel = (snapshot.device?.volume_percent ?? 50) / 100;

  return (
    <div className="visual-player visual-player--spotify">
      <SpotifyModeBanner />

      <div className="visual-player__layout">
        <div className="visual-player__main card">
          <SpotifyNowPlaying
            snapshot={snapshot}
            positionMs={localPositionMs}
            errorMessage={controlError}
          />

          <MetadataVisualizer
            isPlaying={isPlaying}
            accentColor="#1db954"
            artworkUrl={track?.artwork_url ?? null}
            title={track?.title ?? "Spotify"}
          />

          <SeekBar
            positionMs={localPositionMs}
            durationMs={durationMs}
            disabled={!track || controlsDisabled}
            onSeek={(positionMs) => {
              const clamped = clamp(positionMs, 0, durationMs);
              setSeekOverride(clamped);
              void seek(clamped);
            }}
          />

          <PlayerControls
            isPlaying={isPlaying}
            shuffle={snapshot.shuffle ?? false}
            repeatMode="off"
            disabled={controlsDisabled}
            onTogglePlayPause={() => {
              if (isPlaying) {
                void pause();
                return;
              }
              void play();
            }}
            onPrevious={() => {
              void previous();
            }}
            onNext={() => {
              void next();
            }}
            onToggleShuffle={() => undefined}
            onCycleRepeat={() => undefined}
          />

          <VolumeControl
            level={volumeLevel}
            disabled={controlsDisabled}
            onChange={(level) => {
              void setVolume(level);
            }}
          />
        </div>

        {snapshot.recently_played.length > 0 ? (
          <aside className="visual-player__sidebar card">
            <h2>Recently played</h2>
            <ul className="spotify-recent-list">
              {snapshot.recently_played.map((entry) => (
                <li key={`${entry.track.track_id}-${entry.played_at}`}>
                  <strong>{entry.track.title}</strong>
                  <span className="muted">{entry.track.artist_name}</span>
                </li>
              ))}
            </ul>
          </aside>
        ) : null}
      </div>
    </div>
  );
}
