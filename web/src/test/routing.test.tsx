import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { TopNav } from "../components/TopNav";
import { QueryProvider } from "../providers/QueryProvider";
import { createAppRouter } from "../routes/router";
import { createTestQueryClient } from "./test-utils";

function renderWithProviders(ui: React.ReactElement, route = "/") {
  return render(
    <QueryProvider client={createTestQueryClient()}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryProvider>,
  );
}

describe("routing", () => {
  it.each([
    ["/", "Grow your music garden, one song at a time"],
    ["/player", "Player coming soon"],
    ["/garden", "Garden preview"],
    ["/quests", "Quest board"],
    ["/achievements", "Achievement gallery"],
    ["/dev-garden", "Dev garden sandbox"],
  ])("renders %s", async (path, heading) => {
    const testRouter = createAppRouter([path]);

    render(
      <QueryProvider client={createTestQueryClient()}>
        <RouterProvider router={testRouter} />
      </QueryProvider>,
    );

    expect(
      await screen.findByRole("heading", { level: 1, name: heading }),
    ).toBeInTheDocument();
  });

  it("shows a not-found page for unknown routes", async () => {
    const testRouter = createAppRouter(["/does-not-exist"]);

    render(
      <QueryProvider client={createTestQueryClient()}>
        <RouterProvider router={testRouter} />
      </QueryProvider>,
    );

    expect(
      await screen.findByRole("heading", { level: 1, name: /Page not found/i }),
    ).toBeInTheDocument();
  });
});

describe("navigation", () => {
  it("renders primary navigation links", () => {
    renderWithProviders(<TopNav />);

    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Player" })).toHaveAttribute(
      "href",
      "/player",
    );
    expect(screen.getByRole("link", { name: "Garden" })).toHaveAttribute(
      "href",
      "/garden",
    );
    expect(screen.getByRole("link", { name: "Quests" })).toHaveAttribute(
      "href",
      "/quests",
    );
    expect(
      screen.getByRole("link", { name: "Achievements" }),
    ).toHaveAttribute("href", "/achievements");
    expect(screen.getByRole("link", { name: "Dev Garden" })).toHaveAttribute(
      "href",
      "/dev-garden",
    );
  });
});

describe("homepage", () => {
  it("links to the visual player", async () => {
    const testRouter = createAppRouter(["/"]);

    render(
      <QueryProvider client={createTestQueryClient()}>
        <RouterProvider router={testRouter} />
      </QueryProvider>,
    );

    expect(
      await screen.findByRole("link", { name: /Open visual player/i }),
    ).toHaveAttribute("href", "/player");
  });
});
