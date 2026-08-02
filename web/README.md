# MusicBloom Frontend

React + TypeScript UI for the visual player, garden, Recent Blooms (`/history`), favorites, and Dev Garden.

## Setup

```bash
cd web
cp .env.example .env
npm ci
npm run dev
```

Leave `VITE_API_BASE_URL` empty for local development so Vite proxies `/api` and `/static` to `http://127.0.0.1:8000`. Start the FastAPI backend from the repository root first (see the root README).

## Commands

```bash
npm run lint
npm run typecheck
npm run test -- --run
npm run build
```
