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
| Language | Python 3.12 |
| API framework | FastAPI |
| Validation | Pydantic |
| Testing | pytest, pytest-cov |
| Linting | Ruff |
| Type checking | mypy |
| Package layout | `src/` layout |

## Current Development Status

This repository contains the **initial Python backend foundation only**.

**Implemented today:**

- FastAPI application with typed Pydantic response models
- Typed application configuration via `pydantic-settings`
- `GET /` — project metadata
- `GET /api/health` — health check
- `GET /api/v1/health` — versioned health check
- Demo music catalog API with fictional tracks, artists, and albums
- Player session API for demo playback control (metadata only; client-side audio)
- Basic CORS middleware driven by configuration
- Development tooling configuration (pytest, Ruff, mypy)
- Test suite for endpoints, configuration, and application metadata

**Not yet implemented:**

- Frontend / visual player
- Database and persistence
- Spotify integration
- Garden, gamification, quests, Melody Points, BloomBud
- Azure DevOps CI/CD pipelines

## Local Setup

### Prerequisites

- Python 3.12+
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
| `MUSICBLOOM_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed CORS origins |
| `MUSICBLOOM_SECRET_KEY` | *(unset)* | Application secret; **required in production** (minimum 32 characters) |
| `MUSICBLOOM_DATABASE_URL` | *(unset)* | Database connection URL; **required in production** (not yet used) |

**Production validation:** when `MUSICBLOOM_ENVIRONMENT=production`, the application
requires a strong `MUSICBLOOM_SECRET_KEY`, a `MUSICBLOOM_DATABASE_URL`, and enforces
`MUSICBLOOM_DEMO_MODE=false` and `MUSICBLOOM_DEBUG=false`.

Secrets are stored as `SecretStr` values and are masked in settings representations
to avoid accidental exposure in logs.

Settings are cached through `musicbloom.dependencies.get_settings()` and injected
where needed by the application factory.

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
```

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
