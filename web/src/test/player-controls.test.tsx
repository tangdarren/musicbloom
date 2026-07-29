import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PlayerControls } from "../components/player/PlayerControls";

describe("PlayerControls", () => {
  it("calls transport handlers and exposes ARIA labels", async () => {
    const user = userEvent.setup();
    const onTogglePlayPause = vi.fn();
    const onPrevious = vi.fn();
    const onNext = vi.fn();
    const onToggleShuffle = vi.fn();
    const onCycleRepeat = vi.fn();

    render(
      <PlayerControls
        isPlaying={false}
        shuffle={false}
        repeatMode="off"
        onTogglePlayPause={onTogglePlayPause}
        onPrevious={onPrevious}
        onNext={onNext}
        onToggleShuffle={onToggleShuffle}
        onCycleRepeat={onCycleRepeat}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Start playback" }));
    await user.click(screen.getByRole("button", { name: "Previous track" }));
    await user.click(screen.getByRole("button", { name: "Next track" }));
    await user.click(screen.getByRole("button", { name: "Enable shuffle" }));

    expect(onTogglePlayPause).toHaveBeenCalledOnce();
    expect(onPrevious).toHaveBeenCalledOnce();
    expect(onNext).toHaveBeenCalledOnce();
    expect(onToggleShuffle).toHaveBeenCalledOnce();
  });
});
