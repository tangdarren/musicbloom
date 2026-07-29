# Changelog

All notable changes to MusicBloom are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-28

### Added

- FastAPI backend with typed Pydantic models and OpenAPI documentation
- React + TypeScript frontend with garden-themed visual player
- Demo catalog, player session API, and locally generated demo audio
- SQLAlchemy persistence, Alembic migrations, and demo user seeding
- Listening progression, quests, achievements, and garden systems
- Spotify OAuth connection and optional playback metadata/control API
- Azure DevOps pipeline status API and Dev Garden frontend experience
- Azure Pipelines CI workflow for backend and frontend validation
- Docker image, docker-compose demo stack, and portfolio documentation
- 100% backend test coverage requirement and frontend integration tests

### Security

- Encrypted Spotify token storage support
- Secret redaction utilities for Azure DevOps errors
- Production configuration validation for secrets and demo mode

### Known limitations

- Single demo user; no full authentication system yet
- Spotify and Azure DevOps integrations are optional and metadata-only
- No production deployment automation in CI yet
- Quest and achievement pages remain scaffold-level UI in places

[0.1.0]: https://github.com/example/musicbloom/releases/tag/v0.1.0
