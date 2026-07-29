# MusicBloom

**Grow your music garden, one song at a time.**

MusicBloom is a cutesy, gamified visual music player where listening grows a virtual garden, earns Melody Points, completes quests, unlocks decorations, and affects a mascot named **BloomBud**.

## Vision

### Visual Player

A playful, garden-themed music experience that turns everyday listening into something you can see and nurture — not just hear.

### Garden & Gamification

- **Virtual garden** — songs and listening sessions help plants bloom and the garden flourish
- **Melody Points** — earn points for listening and completing activities
- **Quests** — guided goals that reward exploration and consistent listening
- **Decorations** — unlock and place items to personalize your garden
- **BloomBud** — a mascot whose mood and appearance respond to your listening habits

### Spotify Integration *(planned)*

Connect a Spotify account to sync playback, track listening history, and drive garden growth from real music activity.

### Azure DevOps Integration *(planned)*

Use Azure DevOps for CI/CD pipelines, project tracking, and release automation as the project matures.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend language | Python 3.12 |
| API framework | FastAPI |
| Frontend | React, TypeScript, Vite |
| Frontend routing & data | React Router, TanStack Query |
| Validation | Pydantic |
| Backend testing | pytest, pytest-cov |
| Frontend testing | Vitest, React Testing Library |
| Linting | Ruff (Python), ESLint (web) |
| Type checking | mypy (Python), TypeScript (web) |
| Package layout | `src/` layout (Python), `web/` (frontend) |

## Current Development Status

This repository contains the **MusicBloom backend** and an initial **React web interface** under `web/`.

**Implemented today:**

- FastAPI application with typed Pydantic response models
- React + TypeScript frontend scaffold with garden-inspired UI shell
- Typed API client, TanStack Query provider, and `/api/health` status indicator
- Frontend routes for home, player, garden, quests, achievements, and dev garden
- Typed application configuration via `pydantic-settings`
- `GET /` — project metadata
- `GET /api/health` — health check
- `GET /api/v1/health` — versioned health check
- Demo music catalog API with fictional tracks, artists, and albums
- Player session API for demo playback control (metadata only; client-side audio)
- SQLAlchemy 2 persistence with Alembic migrations (SQLite default, PostgreSQL compatible)
- Database-backed player session storage with demo user seeding
- Listening progression system with Melody Points, experience, levels, and streaks
- Quest and achievement system with daily/weekly goals, unlockable rewards, and claim history
- Basic CORS middleware driven by configuration
- Development tooling configuration (pytest, Ruff, mypy)
- Test suite for endpoints, configuration, and application metadata

**Not yet implemented:**

- Full visual player UI (route scaffold only)
- Spotify integration
- Azure DevOps CI/CD pipelines

## Local Setup

### Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- A virtual environment tool (`venv`, `uv`, etc.)

### Install

```bash
# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# Install the package with development dependencies
pip install -e ".[dev]"
```

### Run the API

```bash
# Via the CLI entry point
musicbloom

# Or directly with uvicorn
uvicorn musicbloom.api.app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

- Root: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/api/health`
- Versioned health: `http://127.0.0.1:8000/api/v1/health`
- Interactive docs: `http://127.0.0.1:8000/docs`

### Run the web interface

In a second terminal, start the Vite dev server:

```bash
cd web
cp .env.example .env
npm install
npm run dev
```

The web app will be available at `http://127.0.0.1:5173`.

During local development, Vite proxies `/api/*` requests to the FastAPI backend at
`http://127.0.0.1:8000`, so the health indicator and future API calls work without
extra CORS configuration. For production builds, set `VITE_API_BASE_URL` to your
deployed API origin.

**Frontend routes:**

| Route | Purpose |
|-------|---------|
| `/` | Homepage with MusicBloom overview and player link |
| `/player` | Visual player scaffold (full player not implemented yet) |
| `/garden` | Garden preview shell |
| `/quests` | Quest board scaffold |
| `/achievements` | Achievement gallery scaffold |
| `/dev-garden` | Developer sandbox for garden experiments |

**Frontend commands:**

```bash
cd web
npm run dev       # Start Vite dev server
npm run build     # Production build
npm run preview   # Preview production build
npm run lint      # ESLint
npm run test      # Vitest (add -- --run for CI-style single run)
```

### Configuration

MusicBloom loads settings from environment variables (and an optional `.env` file)
using `pydantic-settings`. All application variables use the `MUSICBLOOM_` prefix.

Copy the example file and adjust values for your environment:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `MUSICBLOOM_ENVIRONMENT` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `MUSICBLOOM_DEBUG` | `true` | Enable debug mode and auto-reload for local development |
| `MUSICBLOOM_DEMO_MODE` | `true` | Enable demo-mode behavior (disabled automatically in production) |
| `MUSICBLOOM_API_HOST` | `0.0.0.0` | Host address for the API server |
| `MUSICBLOOM_API_PORT` | `8000` | Port for the API server |
| `MUSICBLOOM_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed CORS origins |
| `MUSICBLOOM_SECRET_KEY` | *(unset)* | Application secret; **required in production** (minimum 32 characters) |
| `MUSICBLOOM_DATABASE_URL` | `sqlite:///./musicbloom.db` | SQLAlchemy database URL (SQLite or PostgreSQL) |

**Production validation:** when `MUSICBLOOM_ENVIRONMENT=production`, the application
requires a strong `MUSICBLOOM_SECRET_KEY`, a `MUSICBLOOM_DATABASE_URL`, and enforces
`MUSICBLOOM_DEMO_MODE=false` and `MUSICBLOOM_DEBUG=false`.

Secrets are stored as `SecretStr` values and are masked in settings representations
to avoid accidental exposure in logs. Application secrets are never persisted in
the database.

Settings are cached through `musicbloom.dependencies.get_settings()` and injected
where needed by the application factory.

### Database

MusicBloom uses **SQLAlchemy 2** with **Alembic** migrations. The default development
database is local SQLite (`sqlite:///./musicbloom.db`). PostgreSQL is supported by
setting a PostgreSQL-compatible SQLAlchemy URL.

**Initialize and migrate locally:**

```bash
# Apply migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe change"
```

On application startup, the API initializes the configured database and, when
`MUSICBLOOM_DEMO_MODE=true`, seeds a default demo user with an empty player session,
starter garden profile, and initial progress records.

**Persisted entities:**

| Entity | Purpose |
|--------|---------|
| User profile | Local/demo user identity |
| Player session | Playback state, queue, and active track metadata |
| Listening event | Historical listening activity with idempotency keys |
| Garden profile | Garden name, theme, and layout data |
| User progress | Melody Points, experience, level, streaks, and listening totals |
| Track listening state | Per-track anti-exploit progress and completion tracking |
| Melody points transaction | Audited point awards with reasons and explanations |
| Equipped decoration | Decoration slotted in the garden |
| Achievement progress | Achievement completion state |
| Quest progress | Quest status and progress |

Tests use an isolated shared in-memory SQLite database.

Apply migrations after pulling progression changes:

```bash
alembic upgrade head
```

### Listening Progression API

The progression API validates listening events server-side and calculates all
Melody Points and experience awards using deterministic rules in
`musicbloom.progression.policy`. Client-supplied point totals are ignored.

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/listening/events` | Submit a listening event (idempotent) |
| `GET /api/v1/progress` | Combined progression summary |
| `GET /api/v1/stats` | Aggregate listening statistics |
| `GET /api/v1/streak` | UTC-based daily listening streak |

**Listening event types:**

| Type | Behavior |
|------|----------|
| `started` | Records playback start; awards no points |
| `progress` | Awards points for validated listening intervals |
| `completed` | Awards a one-time completion bonus when threshold is met |
| `skipped` | Marks the track skipped; no completion credit |

**Scoring highlights:**

- Progress awards require validated position advances within track duration
- Each track has capped progress rewards to prevent unlimited farming
- Completion bonuses are granted once per track per user
- Daily streak bonuses use UTC calendar dates and are capped per day
- Responses include transparent `awards` explanations for every grant

Example requests:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/listening/events" \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": "demo-track-001",
    "event_type": "progress",
    "position_ms": 60000,
    "idempotency_key": "progress-001"
  }'
curl "http://127.0.0.1:8000/api/v1/progress"
curl "http://127.0.0.1:8000/api/v1/stats"
curl "http://127.0.0.1:8000/api/v1/streak"
```

### Quests, Achievements, and Rewards API

Quest and achievement progress is updated automatically from validated listening
events. Evaluation logic lives in `musicbloom.rewards.evaluator` and is kept
separate from route handlers. Demo quests and achievements are seeded with stable
IDs on database initialization.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/quests` | Daily and weekly quests with progress and completion percentages |
| `GET /api/v1/achievements` | Lifetime achievements with progress and status |
| `POST /api/v1/quests/{quest_id}/claim` | Claim a completed quest reward |
| `POST /api/v1/achievements/{achievement_id}/claim` | Claim a completed achievement reward |
| `GET /api/v1/rewards` | Melody Points balance, unlocked decorations, and claim history |

**Quest lifecycle states:** `locked`, `active`, `completed`, `claimed`

**Seeded demo quests:**

| ID | Cadence | Objective |
|----|---------|-----------|
| `daily-complete-three-tracks` | Daily | Complete three tracks |
| `daily-three-artists` | Daily | Listen to three different artists |
| `daily-thirty-minutes` | Daily | Listen for 30 valid minutes |
| `weekly-three-day-streak` | Weekly | Maintain a three-day streak |
| `weekly-two-genres` | Weekly | Finish tracks from two genres |
| `weekly-focus-session` | Weekly | Complete 60 valid listening minutes |

**Seeded demo achievements:**

| ID | Objective |
|----|-----------|
| `achievement-reach-level-two` | Reach MusicBloom level 2 |
| `achievement-first-bloom` | Complete your first track |

Rewards may grant Melody Points or unlock garden decorations. Completed rewards
cannot be claimed twice; incomplete rewards return `409 Conflict`.

Example requests:

```bash
curl "http://127.0.0.1:8000/api/v1/quests"
curl "http://127.0.0.1:8000/api/v1/achievements"
curl -X POST "http://127.0.0.1:8000/api/v1/quests/daily-complete-three-tracks/claim"
curl -X POST "http://127.0.0.1:8000/api/v1/achievements/achievement-first-bloom/claim"
curl "http://127.0.0.1:8000/api/v1/rewards"
```

### Demo Catalog API

MusicBloom ships with a deterministic demo music catalog so the visual player can
be developed without Spotify credentials. All tracks use **fictional artists,
albums, and audio paths** — no copyrighted music is bundled or referenced.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/tracks` | Paginated demo track collection with optional filters |
| `GET /api/v1/tracks/{track_id}` | Single demo track by stable ID |
| `GET /api/v1/artists` | All demo artists |
| `GET /api/v1/albums` | All demo albums |

**Track list query parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page` | `1` | Page number (minimum 1) |
| `page_size` | `20` | Items per page (1–100) |
| `artist` | — | Filter by artist name or ID |
| `album` | — | Filter by album title or ID |
| `genre` | — | Filter by genre label |
| `mood` | — | Filter by mood (`calm`, `playful`, `dreamy`, `energetic`, `cozy`, `mysterious`) |

Each track includes stable metadata for the future visual player: duration,
artwork, audio source, mood, genre, accent theme colors, and whether it is
playable in demo mode.

Example requests:

```bash
curl "http://127.0.0.1:8000/api/v1/tracks?page=1&page_size=3"
curl "http://127.0.0.1:8000/api/v1/tracks/demo-track-001"
curl "http://127.0.0.1:8000/api/v1/tracks?mood=energetic&genre=brass"
curl "http://127.0.0.1:8000/api/v1/artists"
curl "http://127.0.0.1:8000/api/v1/albums"
```

### Player Session API

The player session API tracks **playback metadata only**. It does not stream audio;
the future browser client will play demo catalog files locally based on the returned
`audio` references.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/player` | Current player session state |
| `PUT /api/v1/player/play` | Play a track or resume/start queue playback |
| `PUT /api/v1/player/pause` | Pause the active track |
| `PUT /api/v1/player/seek` | Seek within the active track |
| `PUT /api/v1/player/volume` | Set normalized volume (`0.0`–`1.0`) |
| `PUT /api/v1/player/shuffle` | Enable or disable shuffle mode |
| `PUT /api/v1/player/repeat` | Set repeat mode (`off`, `one`, `all`) |
| `POST /api/v1/player/next` | Advance to the next queue item |
| `POST /api/v1/player/previous` | Restart or move to the previous queue item |
| `POST /api/v1/player/queue` | Append a demo catalog track to the queue |
| `DELETE /api/v1/player/queue/{track_id}` | Remove a track from the queue |

Example requests:

```bash
curl "http://127.0.0.1:8000/api/v1/player"
curl -X PUT "http://127.0.0.1:8000/api/v1/player/play" \
  -H "Content-Type: application/json" \
  -d '{"track_id":"demo-track-001"}'
curl -X POST "http://127.0.0.1:8000/api/v1/player/queue" \
  -H "Content-Type: application/json" \
  -d '{"track_id":"demo-track-002"}'
curl -X PUT "http://127.0.0.1:8000/api/v1/player/seek" \
  -H "Content-Type: application/json" \
  -d '{"position_ms":30000}'
curl -X POST "http://127.0.0.1:8000/api/v1/player/next"
```

Duplicate queue entries are rejected unless `allow_duplicate` is set to `true`.
Seek positions and volume values are validated; unknown tracks and queue items
return `404`, and invalid playback actions return useful `4xx` responses.

## Validation Commands

Run these from the project root with your virtual environment activated:

```bash
python -m pytest
python -m ruff check .
python -m mypy src
cd web && npm run lint
cd web && npm run test -- --run
cd web && npm run build
```

Install frontend dependencies first with `cd web && npm install` if you have not
already done so.

## Project Structure

```
musicbloom/
├── .cursor/
│   └── rules/
│       └── manual-git.mdc
├── src/
│   └── musicbloom/
│       ├── __init__.py
│       ├── constants.py
│       ├── config.py
│       ├── dependencies.py
│       ├── main.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── catalog.py
│       │   └── player.py
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── demo_catalog.py
│       │   ├── demo_data.py
│       │   ├── in_memory_player.py
│       │   └── player.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── catalog.py
│       │   ├── player.py
│       │   └── player_errors.py
│       └── api/
│           ├── __init__.py
│           ├── app.py
│           ├── schemas.py
│           └── v1/
│               ├── __init__.py
│               ├── router.py
│               ├── routes/
│               │   ├── __init__.py
│               │   ├── albums.py
│               │   ├── artists.py
│               │   ├── player.py
│               │   └── tracks.py
│               └── schemas/
│                   ├── __init__.py
│                   ├── catalog.py
│                   └── player.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_catalog_api.py
│   ├── test_catalog_models.py
│   ├── test_catalog_repository.py
│   ├── test_catalog_service.py
│   ├── test_config.py
│   ├── test_player_api.py
│   ├── test_player_models.py
│   ├── test_player_repository.py
│   └── test_player_service.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## License

MIT
