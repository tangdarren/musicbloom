interface FavoriteToggleButtonProps {
  trackTitle: string;
  isFavorited: boolean;
  disabled?: boolean;
  onToggle: () => void;
}

export function FavoriteToggleButton({
  trackTitle,
  isFavorited,
  disabled = false,
  onToggle,
}: FavoriteToggleButtonProps) {
  const label = isFavorited
    ? `Remove ${trackTitle} from favorites`
    : `Add ${trackTitle} to favorites`;

  return (
    <button
      type="button"
      className={
        isFavorited
          ? "favorite-toggle favorite-toggle--active"
          : "favorite-toggle"
      }
      aria-label={label}
      aria-pressed={isFavorited}
      disabled={disabled}
      onClick={onToggle}
    >
      <span aria-hidden="true">✿</span>
    </button>
  );
}
