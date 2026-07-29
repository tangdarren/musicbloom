/** Garden and decoration API types. */

export type GardenMood = "serene" | "cheerful" | "blooming";

export type ProgressStatus = "locked" | "active" | "completed" | "claimed";

export interface ExperienceProgress {
  total_experience: number;
  experience_in_level: number;
  experience_to_next_level: number;
}

export interface UserLevel {
  level: number;
  experience: ExperienceProgress;
}

export interface DailyListeningStreak {
  current_days: number;
  last_listening_utc_date: string | null;
  bonus_points_awarded_today: number;
  daily_bonus_cap: number;
}

export interface GardenProfileView {
  garden_name: string;
  theme: string;
}

export interface ArtistFlower {
  artist_id: string;
  artist_name: string;
  completions: number;
  bloom_stage: number;
}

export interface ListeningMilestonePlant {
  id: string;
  title: string;
  description: string;
  target: number;
  progress: number;
  unlocked: boolean;
}

export interface DecorationDefinition {
  id: string;
  name: string;
  description: string;
  slot: string;
}

export interface DecorationUnlock {
  decoration: DecorationDefinition;
  unlocked_at: string;
}

export interface EquippedDecorationView {
  decoration: DecorationDefinition;
  slot: string;
  equipped_at: string;
}

export interface RecentAchievement {
  achievement_id: string;
  title: string;
  status: ProgressStatus;
  completed_at: string | null;
}

export interface GardenState {
  profile: GardenProfileView;
  mood: GardenMood;
  level: UserLevel;
  melody_points: number;
  streak: DailyListeningStreak;
  artist_flowers: ArtistFlower[];
  milestone_plants: ListeningMilestonePlant[];
  unlocked_decorations: DecorationUnlock[];
  equipped_decorations: EquippedDecorationView[];
  recent_achievements: RecentAchievement[];
  tracks_completed: number;
  total_listening_minutes: number;
}

export interface DecorationCatalogEntry {
  decoration: DecorationDefinition;
  unlocked: boolean;
  equipped: boolean;
}

export interface EquipDecorationResult {
  decoration: DecorationDefinition;
  slot: string;
  equipped_at: string;
}
