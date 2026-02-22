# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a **Turborepo monorepo** with two distinct technology stacks:

- `apps/web` — Next.js 16 frontend (React 19, TypeScript)
- `apps/docs` — Next.js documentation site
- `apps/airflow` — Apache Airflow 3 pipeline for running [Helical](https://github.com/helical-ai/helical) bioinformatics model inference
- `packages/ui` — Shared React component library (`@repo/ui`)
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
```

Run for a specific app (e.g., web only):

```bash
npx turbo run dev --filter=web
npx turbo run build --filter=web
```

## Airflow (Python) Commands

The Airflow app uses **uv** for dependency management and **Docker Compose** for local execution. Python version is pinned in `apps/airflow/.python-version`.

```bash
# Start the full Airflow stack (from repo root or apps/airflow)
docker compose up --build

# Or from repo root (docker-compose.yaml includes the airflow compose file)
docker compose up --build
```

The Airflow UI is available at `http://localhost:8080` (default credentials: `airflow`/`airflow`).

To add Python dependencies available inside Docker containers, edit `apps/airflow/docker-requirements.txt` (used in the Docker image build). The `pyproject.toml` is for local development with uv.

```bash
# Local dev environment (uv)
cd apps/airflow
uv sync
uv run python main.py
```

## Architecture Notes

### Airflow DAGs

DAGs live in `apps/airflow/dags/`. The primary DAG (`execute_inference_helical_model_dag`) runs Helical genomic model inference (currently Geneformer) on HuggingFace datasets and writes embeddings to `dags/files/output.csv`. Heavy imports (torch, helical, datasets) are done inside the task function to avoid DAG parse-time overhead.

The Airflow stack uses CeleryExecutor with Redis as broker and PostgreSQL as backend. The custom Docker image extends `apache/airflow:3.1.7-python3.10` and installs `helical` from `docker-requirements.txt`.

### Shared UI Package

`packages/ui` exports React components (`button`, `card`, `code`) consumed by `apps/web` and `apps/docs` via the `@repo/ui` workspace alias.
