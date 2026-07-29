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
- `GET /` — project metadata
- `GET /api/health` — health check
- Development tooling configuration (pytest, Ruff, mypy)
- Test suite for endpoints and application metadata

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
- Interactive docs: `http://127.0.0.1:8000/docs`

### Environment Variables

Copy the example file when you need to configure future integrations:

```bash
cp .env.example .env
```

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
│       ├── main.py
│       └── api/
│           ├── __init__.py
│           └── app.py
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## License

MIT
