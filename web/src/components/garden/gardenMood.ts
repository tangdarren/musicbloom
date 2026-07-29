import type { GardenMood } from "../../api/gardenTypes";

export function moodLabel(mood: GardenMood, resting: boolean): string {
  if (resting) {
    return "Resting";
  }

  switch (mood) {
    case "blooming":
      return "Blooming";
    case "cheerful":
      return "Cheerful";
    default:
      return "Serene";
  }
}
