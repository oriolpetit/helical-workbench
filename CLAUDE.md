# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Repository Structure

This is a **Turborepo monorepo** with the following apps:

- `apps/web` — Next.js 16 frontend (React 19, TypeScript, Mantine 8)
- `apps/backend` — FastAPI backend bridging the web UI and Airflow pipeline
- `apps/airflow` — Apache Airflow 3 pipeline for
  running [Helical](https://github.com/helical-ai/helical) bioinformatics model inference
- `packages/eslint-config` — Shared ESLint config (`@repo/eslint-config`)
- `packages/typescript-config` — Shared TypeScript config (`@repo/typescript-config`)

## JavaScript/TypeScript Commands

Run from the repo root:

```bash
npm run dev          # Start all apps in dev mode (Turborepo)
npm run build        # Build all apps
npm run lint         # Lint all packages
npm run check-types  # Type-check all packages
npm run format       # Prettier format all TS/TSX/MD files
npm run release    # Run build, check-types, test, and lint (full release check)
```

Run for a specific app (e.g., web only):

```bash
npx turbo run dev --filter=web
```

## Backend (Python — FastAPI)

`apps/backend` is a FastAPI app using **uv**. Runs on port 8000.

After changing the API, regenerate the TypeScript client used by `apps/web`:

```bash
# From apps/backend
npm run generate-openapi          # Exports build/openapi_spec.json

# From apps/web
npm run generate-backend-ts-client  # Writes typed client to app/services/backend/
```

The generated client in `apps/web/app/services/backend/` should be committed alongside API changes.

## Airflow (Python)

The Airflow app uses **uv** for dependency management and **Docker Compose** for local execution.
Python version is pinned in `apps/airflow/.python-version`.

```bash
# Start the full stack (from repo root)
docker compose up --build
```

The Airflow UI is available at `http://localhost:8080` (credentials: `airflow`/`airflow`).

To add Python dependencies for Docker, edit `apps/airflow/requirements.txt` (generated from
`pyproject.toml` via `uv export`) and rebuild. For local dev, edit `pyproject.toml` and run
`uv sync`.

```bash
# Local dev
cd apps/airflow
uv sync
uv run python main.py
```

## Architecture Notes

### Backend

Layered design: `Routes → Service → Client`

- **Routes** (`api/routes/`) — HTTP layer, request validation, response serialisation
- **Service** (`services/`) — business logic, job state management
- **Client** (`clients/`) — Airflow REST API integration

Key env vars: `AIRFLOW_HOST`, `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD`, `RESULTS_DIR`. Results are
shared with the Airflow container via a Docker volume.

### Airflow DAGs

DAGs live in `apps/airflow/dags/`. The primary DAG (`execute_inference_helical_model_dag`) runs
Helical genomic model inference on HuggingFace datasets and writes embeddings as CSV to
`results/<run_id>.csv`. Heavy imports (torch, helical, datasets) are done inside task functions to
avoid DAG parse-time overhead.

The stack uses CeleryExecutor with Redis as broker and PostgreSQL as backend. The custom Docker
image extends `apache/airflow:3.1.7-python3.10`.

### Web Frontend

`apps/web` is a static Next.js export served by Nginx in Docker. `NEXT_PUBLIC_API_URL` is baked in
at build time (defaults to `http://localhost:8000`).
