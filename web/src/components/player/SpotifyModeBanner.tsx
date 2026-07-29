export function SpotifyModeBanner() {
  return (
    <div className="spotify-mode-banner" role="note" aria-label="Spotify mode active">
      <strong>Spotify mode</strong>
      <span>
        MusicBloom displays Spotify metadata and playback state only. Audio plays
        through your Spotify app or device — nothing is downloaded or proxied.
      </span>
    </div>
  );
}
