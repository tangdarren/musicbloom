import { Outlet } from "react-router-dom";

import { PlaybackSignalsProvider } from "../player/PlaybackSignalsContext";
import { TopNav } from "./TopNav";

export function AppShell() {
  return (
    <PlaybackSignalsProvider>
      <div className="app-shell">
        <a className="skip-link" href="#main-content">
          Skip to main content
        </a>
        <TopNav />
        <main className="app-shell__main" id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
        <footer className="app-shell__footer">
          <p>
            MusicBloom — a cutesy garden music player. Demo catalog only; no
            Spotify branding here.
          </p>
        </footer>
      </div>
    </PlaybackSignalsProvider>
  );
}
