import { Outlet } from "react-router-dom";

import { PlaybackSignalsProvider } from "../player/PlaybackSignalsContext";
import { TopNav } from "./TopNav";

export function AppShell() {
  return (
    <PlaybackSignalsProvider>
      <div className="app-shell">
        <TopNav />
        <main className="app-shell__main" id="main-content">
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
