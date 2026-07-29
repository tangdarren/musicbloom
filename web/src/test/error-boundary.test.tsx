import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ErrorBoundary } from "../components/ErrorBoundary";

function BrokenComponent(): never {
  throw new Error("Petals everywhere");
}

describe("ErrorBoundary", () => {
  it("renders a recovery screen when a child throws", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(/Petals everywhere/i);
    expect(
      screen.getByRole("heading", { name: /Something sprouted unexpectedly/i }),
    ).toBeInTheDocument();

    consoleError.mockRestore();
  });

  it("allows retrying after an error", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const user = userEvent.setup();
    let shouldThrow = true;

    function MaybeBroken() {
      if (shouldThrow) {
        throw new Error("Temporary wilt");
      }

      return <p>Recovered bloom</p>;
    }

    render(
      <ErrorBoundary>
        <MaybeBroken />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();

    shouldThrow = false;
    await user.click(screen.getByRole("button", { name: /Try again/i }));

    expect(await screen.findByText(/Recovered bloom/i)).toBeInTheDocument();

    consoleError.mockRestore();
  });
});
