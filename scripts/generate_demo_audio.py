"""Generate lightweight demo WAV tones for browser playback."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44_100
DURATION_SECONDS = 14

TRACK_FREQUENCIES: dict[str, float] = {
    "morning-dew-waltz": 392.0,
    "mossy-footsteps": 349.23,
    "bubblegum-breeze": 523.25,
    "starlit-sprinkler": 440.0,
    "fern-fanfare": 587.33,
}


def generate_tone(path: Path, frequency_hz: float) -> None:
    """Write a soft sine tone WAV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_count = SAMPLE_RATE * DURATION_SECONDS

    with wave.open(str(path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)

        for index in range(sample_count):
            time_seconds = index / SAMPLE_RATE
            fade = min(1.0, time_seconds * 3) * min(
                1.0,
                (DURATION_SECONDS - time_seconds) * 3,
            )
            sample = int(
                32_767
                * 0.28
                * fade
                * math.sin(2 * math.pi * frequency_hz * time_seconds),
            )
            wav_file.writeframes(struct.pack("<h", sample))


def main() -> None:
    output_dir = Path(__file__).resolve().parents[1] / "static" / "demo" / "audio"
    for slug, frequency in TRACK_FREQUENCIES.items():
        generate_tone(output_dir / f"{slug}.wav", frequency)
        print(f"Wrote {output_dir / f'{slug}.wav'}")


if __name__ == "__main__":
    main()
