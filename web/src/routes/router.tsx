import type { RouteObject } from "react-router-dom";
import { createBrowserRouter, createMemoryRouter } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { AchievementsPage } from "../pages/AchievementsPage";
import { DevGardenPage } from "../pages/DevGardenPage";
import { GardenPage } from "../pages/GardenPage";
import { HomePage } from "../pages/HomePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { PlayerPage } from "../pages/PlayerPage";
import { QuestsPage } from "../pages/QuestsPage";

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <AppShell />,
    errorElement: <NotFoundPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "player", element: <PlayerPage /> },
      { path: "garden", element: <GardenPage /> },
      { path: "quests", element: <QuestsPage /> },
      { path: "achievements", element: <AchievementsPage /> },
      { path: "dev-garden", element: <DevGardenPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(appRoutes);

export function createAppRouter(initialEntries: string[]) {
  return createMemoryRouter(appRoutes, { initialEntries });
}
