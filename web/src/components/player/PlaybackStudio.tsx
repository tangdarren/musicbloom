import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../../api/client";
import { usePlaybackMode } from "../../player/PlaybackModeContext";
import { PlaybackModeSelector } from "./PlaybackModeSelector";
import { SpotifyVisualPlayer } from "./SpotifyVisualPlayer";
import { VisualPlayer } from "./VisualPlayer";

export function PlaybackStudio() {
  const { mode, setMode } = usePlaybackMode();
  const spotifyStatusQuery = useQuery({
    queryKey: ["spotify", "status"],
    queryFn: () => apiClient.getSpotifyStatus(),
  });

  const spotifyStatus = spotifyStatusQuery.data;
  const spotifyConnected = spotifyStatus?.status === "connected";
  const spotifyConfigured = spotifyStatus?.configured !== false;

  return (
    <div className="playback-studio">
      <PlaybackModeSelector
        mode={mode}
        spotifyConnected={spotifyConnected}
        spotifyConfigured={spotifyConfigured}
        onChange={setMode}
      />
      {mode === "demo" ? <VisualPlayer /> : <SpotifyVisualPlayer />}
    </div>
  );
}
