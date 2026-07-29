# Contributing to MusicBloom

Thank you for your interest in MusicBloom. This project is designed as a
portfolio-ready reference application, so clarity and test coverage matter.

## Development setup

1. Install Python 3.12 and Node.js 20.
2. Create a virtual environment and install backend dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Install frontend dependencies:

```bash
cd web
npm ci
```

4. Copy environment files:

```bash
cp .env.example .env
cp web/.env.example web/.env
```

## Validation before opening a pull request

Run the full validation suite from the repository root:

```bash
python -m ruff check .
python -m mypy src
python -m pytest
cd web && npm run lint
cd web && npm run typecheck
cd web && npm run test -- --run
cd web && npm run build
python -m build
docker build -t musicbloom:local .
```

## Coding guidelines

- Match existing naming, typing, and error-handling conventions.
- Keep demo mode working without Spotify or Azure DevOps credentials.
- Never commit secrets, tokens, or personal `.env` files.
- Prefer focused changes with tests for new behavior.
- Maintain 100% backend coverage for `src/musicbloom`.

## Pull requests

- Target `main`.
- Describe the user-facing impact and any setup changes.
- Confirm validation commands pass locally or in Azure Pipelines.
- Link related issues when applicable.

## Reporting bugs

Include reproduction steps, expected behavior, actual behavior, and relevant
logs. Do not include access tokens or personal credentials.
