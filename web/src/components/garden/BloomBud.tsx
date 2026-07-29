interface BloomBudProps {
  resting: boolean;
  celebrating: boolean;
  reducedMotion: boolean;
}

export function BloomBud({
  resting,
  celebrating,
  reducedMotion,
}: BloomBudProps) {
  const className = [
    "bloom-bud",
    resting ? "bloom-bud--resting" : "",
    celebrating && !reducedMotion ? "bloom-bud--celebrating" : "",
    reducedMotion ? "bloom-bud--calm" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} aria-label="BloomBud mascot" role="img">
      <svg viewBox="0 0 120 140" className="bloom-bud__svg" aria-hidden="true">
        <ellipse cx="60" cy="118" rx="34" ry="10" fill="#c8e6c9" />
        <path
          d="M48 118 C48 92, 72 92, 72 118"
          fill="#7bc47f"
          stroke="#3f8d5d"
          strokeWidth="2"
        />
        <circle cx="60" cy="68" r="30" fill="#fff7fb" stroke="#e7a6c8" strokeWidth="3" />
        <ellipse cx="48" cy="64" rx="6" ry="8" fill="#23402c" />
        <ellipse cx="72" cy="64" rx="6" ry="8" fill="#23402c" />
        <circle cx="50" cy="62" r="2" fill="#ffffff" />
        <circle cx="74" cy="62" r="2" fill="#ffffff" />
        <path
          d="M52 78 Q60 86 68 78"
          fill="none"
          stroke="#e7a6c8"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <ellipse cx="38" cy="72" rx="8" ry="5" fill="#ffd8eb" opacity="0.7" />
        <ellipse cx="82" cy="72" rx="8" ry="5" fill="#ffd8eb" opacity="0.7" />
        <path
          d="M60 38 C52 18, 38 24, 44 40 C36 34, 34 48, 46 46 C42 58, 56 54, 60 44"
          fill="#7bc47f"
          stroke="#3f8d5d"
          strokeWidth="2"
        />
        <path
          d="M60 44 C68 24, 82 30, 76 46 C84 40, 86 54, 74 52 C78 64, 64 60, 60 50"
          fill="#7bc47f"
          stroke="#3f8d5d"
          strokeWidth="2"
        />
        <circle cx="60" cy="34" r="6" fill="#f4c9de" />
      </svg>
      <p className="bloom-bud__label">BloomBud</p>
    </div>
  );
}
