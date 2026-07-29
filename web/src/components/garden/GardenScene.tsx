import type {
  ArtistFlower,
  DecorationCatalogEntry,
  EquippedDecorationView,
  ListeningMilestonePlant,
} from "../../api/gardenTypes";

interface GardenSceneProps {
  flowers: ArtistFlower[];
  plants: ListeningMilestonePlant[];
  equipped: EquippedDecorationView[];
  swaying: boolean;
  bloomingFlowerId: string | null;
  streakEffect: boolean;
  reducedMotion: boolean;
}

function DecorationGlyph({ decorationId }: { decorationId: string }) {
  if (decorationId.includes("lantern")) {
    return (
      <svg viewBox="0 0 48 64" className="garden-scene__decoration-svg" aria-hidden="true">
        <rect x="18" y="40" width="12" height="18" rx="2" fill="#8d6e63" />
        <path d="M12 40 H36 L30 18 H18 Z" fill="#fff4df" stroke="#e7a6c8" strokeWidth="2" />
        <circle cx="24" cy="28" r="6" fill="#ffe082" />
      </svg>
    );
  }

  if (decorationId.includes("fountain")) {
    return (
      <svg viewBox="0 0 64 64" className="garden-scene__decoration-svg" aria-hidden="true">
        <ellipse cx="32" cy="52" rx="24" ry="8" fill="#b3e5fc" />
        <path d="M20 52 V28 H44 V52" fill="#90caf9" stroke="#4f6d59" strokeWidth="2" />
        <path d="M32 10 C24 22, 24 34, 32 28 C40 34, 40 22, 32 10" fill="#81d4fa" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 48 64" className="garden-scene__decoration-svg" aria-hidden="true">
      <path d="M24 58 V34" stroke="#3f8d5d" strokeWidth="4" strokeLinecap="round" />
      <ellipse cx="24" cy="24" rx="14" ry="18" fill="#7bc47f" />
      <ellipse cx="24" cy="18" rx="6" ry="8" fill="#a5d6a7" />
    </svg>
  );
}

function FlowerGlyph({
  flower,
  blooming,
  reducedMotion,
}: {
  flower: ArtistFlower;
  blooming: boolean;
  reducedMotion: boolean;
}) {
  const stage = flower.bloom_stage;
  const className = [
    "garden-scene__flower",
    blooming && !reducedMotion ? "garden-scene__flower--blooming" : "",
    `garden-scene__flower--stage-${stage}`,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} title={`${flower.artist_name} (${flower.completions})`}>
      <svg viewBox="0 0 48 64" aria-hidden="true">
        <path d="M24 58 V36" stroke="#3f8d5d" strokeWidth="3" strokeLinecap="round" />
        <circle cx="24" cy="24" r={8 + stage * 2} fill="#f4c9de" opacity={0.4 + stage * 0.15} />
        <circle cx="16" cy="22" r={4 + stage} fill="#f8bbd0" />
        <circle cx="32" cy="22" r={4 + stage} fill="#f8bbd0" />
        <circle cx="24" cy="14" r={4 + stage} fill="#f48fb1" />
        <circle cx="24" cy="24" r="5" fill="#ffe082" />
      </svg>
      <span className="garden-scene__flower-label">{flower.artist_name}</span>
    </div>
  );
}

function PlantGlyph({
  plant,
  swaying,
  reducedMotion,
}: {
  plant: ListeningMilestonePlant;
  swaying: boolean;
  reducedMotion: boolean;
}) {
  const className = [
    "garden-scene__plant",
    plant.unlocked ? "garden-scene__plant--grown" : "garden-scene__plant--seedling",
    swaying && !reducedMotion ? "garden-scene__plant--swaying" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} title={plant.title}>
      <svg viewBox="0 0 40 56" aria-hidden="true">
        <path d="M20 50 V28" stroke="#3f8d5d" strokeWidth="3" strokeLinecap="round" />
        {plant.unlocked ? (
          <>
            <ellipse cx="20" cy="18" rx="12" ry="14" fill="#7bc47f" />
            <ellipse cx="14" cy="24" rx="6" ry="8" fill="#a5d6a7" />
            <ellipse cx="26" cy="24" rx="6" ry="8" fill="#a5d6a7" />
          </>
        ) : (
          <circle cx="20" cy="42" r="4" fill="#8d6e63" />
        )}
      </svg>
      <span className="garden-scene__plant-label">{plant.title}</span>
    </div>
  );
}

export function GardenScene({
  flowers,
  plants,
  equipped,
  swaying,
  bloomingFlowerId,
  streakEffect,
  reducedMotion,
}: GardenSceneProps) {
  const slots = ["north", "center", "south"] as const;

  return (
    <div
      className={[
        "garden-scene",
        streakEffect && !reducedMotion ? "garden-scene--streak" : "",
        reducedMotion ? "garden-scene--calm" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Interactive garden plot"
    >
      <div className="garden-scene__sky" aria-hidden="true" />
      <div className="garden-scene__ground">
        {slots.map((slot) => {
          const decoration = equipped.find((item) => item.slot === slot);
          return (
            <div
              key={slot}
              className={`garden-scene__slot garden-scene__slot--${slot}`}
            >
              {decoration ? (
                <DecorationGlyph decorationId={decoration.decoration.id} />
              ) : (
                <span className="garden-scene__slot-empty" aria-hidden="true" />
              )}
            </div>
          );
        })}

        <div className="garden-scene__flowers">
          {flowers.length === 0 ? (
            <p className="garden-scene__empty">
              Complete tracks to grow artist flowers here.
            </p>
          ) : (
            flowers.map((flower) => (
              <FlowerGlyph
                key={flower.artist_id}
                flower={flower}
                blooming={bloomingFlowerId === flower.artist_id}
                reducedMotion={reducedMotion}
              />
            ))
          )}
        </div>

        <div className="garden-scene__plants">
          {plants.map((plant) => (
            <PlantGlyph
              key={plant.id}
              plant={plant}
              swaying={swaying}
              reducedMotion={reducedMotion}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export function DecorationPanel({
  decorations,
  onEquip,
  onUnequip,
  busyId,
}: {
  decorations: DecorationCatalogEntry[];
  onEquip: (decorationId: string) => void;
  onUnequip: (decorationId: string) => void;
  busyId: string | null;
}) {
  if (decorations.length === 0) {
    return (
      <p className="garden-panel__empty">
        Complete quests and achievements to unlock decorations.
      </p>
    );
  }

  return (
    <ul className="garden-decorations">
      {decorations.map(({ decoration, unlocked, equipped }) => (
        <li key={decoration.id} className="garden-decorations__item">
          <div>
            <strong>{decoration.name}</strong>
            <p className="muted">{decoration.description}</p>
            <p className="garden-decorations__meta">
              Slot: {decoration.slot}
              {!unlocked ? " · Locked" : equipped ? " · Equipped" : " · Unlocked"}
            </p>
          </div>
          {unlocked ? (
            equipped ? (
              <button
                type="button"
                className="button button--secondary"
                disabled={busyId === decoration.id}
                onClick={() => onUnequip(decoration.id)}
              >
                Unequip
              </button>
            ) : (
              <button
                type="button"
                className="button"
                disabled={busyId === decoration.id}
                onClick={() => onEquip(decoration.id)}
              >
                Equip
              </button>
            )
          ) : (
            <span className="garden-decorations__locked" aria-label="Locked">
              Locked
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
