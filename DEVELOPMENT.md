# Development Guide

This document covers everything needed to contribute to or extend Helical Workbench.

## Repository Structure

This is a **Turborepo monorepo** with the following apps and packages:

| Path                                     | Description                                               |
|------------------------------------------|-----------------------------------------------------------|
| [`apps/web`](apps/web/README.md)         | Next.js 16 frontend (React 19, TypeScript)                |
| [`apps/backend`](apps/backend/README.md) | FastAPI backend that bridges the web UI and Airflow       |
| [`apps/airflow`](apps/airflow/README.md) | Apache Airflow 3 pipeline running Helical model inference |
| `packages/eslint-config`                 | Shared ESLint config (`@repo/eslint-config`)              |
| `packages/typescript-config`             | Shared TypeScript config (`@repo/typescript-config`)      |

## Prerequisites

- [Node.js](https://nodejs.org/) (see `.nvmrc` or `engines` field in `package.json`)
- [Turbo](https://turborepo.dev/docs/getting-started/installation#global-installation) — global
  installation recommended (`npm install -g turbo`)
- [Docker](https://docs.docker.com/get-docker/) — required for Airflow and full-stack local runs
- [uv](https://docs.astral.sh/uv/) — for local Python development in `apps/airflow` and
  `apps/backend`

## Running the Full Stack

The root `docker-compose.yaml` includes all services (web, backend, Airflow):

```bash
docker compose up --build
```

| Service           | URL                   |
|-------------------|-----------------------|
| Web UI            | http://localhost:3000 |
| Backend API       | http://localhost:8000 |
| Airflow dashboard | http://localhost:8080 |

Stop everything with:

```bash
docker compose down
```

## JavaScript / TypeScript

Run from the repo root:

```bash
npm run dev          # Start all apps in dev mode. This allows to quickly iterate by having changes automatically refresh (hotswapped)
npm run build        # Build all apps
npm run lint         # Lint all packages
npm run check-types  # Type-check all packages
npm run format       # Prettier format all TS/TSX/MD files
npm run release    # Run build, check-types, test, and lint (full release check)
```

For app-specific development instructions, see each app's README linked in the repository structure
table above.

> **Note:** After stopping `npm run dev`, the Airflow background services keep running. To fully
> shut them down:
> ```bash
> cd apps/airflow && docker compose down
> ```
