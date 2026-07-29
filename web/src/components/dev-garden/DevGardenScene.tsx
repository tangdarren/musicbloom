import type { DevGardenVisualState } from "./devGardenState";

interface DevGardenSceneProps {
  visualState: DevGardenVisualState;
  reducedMotion: boolean;
  sceneDescription: string;
}

export function DevGardenScene({
  visualState,
  reducedMotion,
  sceneDescription,
}: DevGardenSceneProps) {
  const sceneClassName = [
    "dev-garden-scene",
    `dev-garden-scene--${visualState}`,
    reducedMotion ? "dev-garden-scene--calm" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={sceneClassName}
      role="img"
      aria-label={sceneDescription}
      data-testid="dev-garden-scene"
      data-visual-state={visualState}
    >
      <div className="dev-garden-scene__sky" aria-hidden="true">
        {visualState === "partially_succeeded" ? (
          <div className="dev-garden-scene__clouds">
            <span className="dev-garden-scene__cloud" />
            <span className="dev-garden-scene__cloud dev-garden-scene__cloud--two" />
          </div>
        ) : null}
      </div>

      <div className="dev-garden-scene__ground" aria-hidden="true">
        <div
          className={[
            "dev-garden-scene__plant",
            visualState === "failed" ? "dev-garden-scene__plant--wilted" : "",
            visualState === "succeeded" ? "dev-garden-scene__plant--healthy" : "",
            visualState === "empty" ? "dev-garden-scene__plant--empty-pot" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <span className="dev-garden-scene__stem" />
          <span className="dev-garden-scene__leaf dev-garden-scene__leaf--left" />
          <span className="dev-garden-scene__leaf dev-garden-scene__leaf--right" />
          <span className="dev-garden-scene__pot" />
        </div>

        {visualState === "failed" ? (
          <div className="dev-garden-scene__error-sign" aria-hidden="true">
            <span className="dev-garden-scene__error-icon">!</span>
            <span className="dev-garden-scene__error-text">Build failed</span>
          </div>
        ) : null}

        {visualState === "running" ? (
          <div className="dev-garden-scene__laptop" aria-hidden="true">
            <span className="dev-garden-scene__laptop-screen" />
            <span className="dev-garden-scene__laptop-base" />
          </div>
        ) : null}

        {visualState === "succeeded" ? (
          <div className="dev-garden-scene__water-can" aria-hidden="true">
            <span className="dev-garden-scene__water-stream" />
          </div>
        ) : null}

        {visualState === "canceled" ? (
          <div
            className="dev-garden-scene__stored-can"
            aria-hidden="true"
            title="Watering can stored"
          />
        ) : null}
      </div>

      <DevGardenBloomBud
        visualState={visualState}
        reducedMotion={reducedMotion}
      />
    </div>
  );
}

interface DevGardenBloomBudProps {
  visualState: DevGardenVisualState;
  reducedMotion: boolean;
}

function DevGardenBloomBud({
  visualState,
  reducedMotion,
}: DevGardenBloomBudProps) {
  const className = [
    "dev-garden-bud",
    visualState === "empty" ? "dev-garden-bud--sleeping" : "",
    visualState === "running" ? "dev-garden-bud--working" : "",
    visualState === "succeeded" ? "dev-garden-bud--watering" : "",
    visualState === "canceled" ? "dev-garden-bud--stowing" : "",
    !reducedMotion && visualState === "running"
      ? "dev-garden-bud--typing"
      : "",
    reducedMotion ? "dev-garden-bud--calm" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} aria-hidden="true">
      <svg viewBox="0 0 120 140" className="dev-garden-bud__svg">
        <ellipse cx="60" cy="118" rx="34" ry="10" fill="#c8e6c9" />
        <path
          d="M48 118 C48 92, 72 92, 72 118"
          fill="#7bc47f"
          stroke="#3f8d5d"
          strokeWidth="2"
        />
        <circle cx="60" cy="68" r="30" fill="#fff7fb" stroke="#e7a6c8" strokeWidth="3" />
        {visualState === "empty" ? (
          <>
            <path d="M44 62 L52 62" stroke="#23402c" strokeWidth="2" />
            <path d="M76 62 L68 62" stroke="#23402c" strokeWidth="2" />
          </>
        ) : (
          <>
            <ellipse cx="48" cy="64" rx="6" ry="8" fill="#23402c" />
            <ellipse cx="72" cy="64" rx="6" ry="8" fill="#23402c" />
            <circle cx="50" cy="62" r="2" fill="#ffffff" />
            <circle cx="74" cy="62" r="2" fill="#ffffff" />
          </>
        )}
        <path
          d={
            visualState === "failed"
              ? "M52 82 Q60 74 68 82"
              : "M52 78 Q60 86 68 78"
          }
          fill="none"
          stroke="#e7a6c8"
          strokeWidth="3"
          strokeLinecap="round"
        />
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
        {visualState === "empty" ? (
          <text x="78" y="52" fontSize="16">
            z
          </text>
        ) : null}
      </svg>
    </div>
  );
}
