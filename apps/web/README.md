# Web — Frontend

Next.js 16 frontend (React 19, TypeScript). Provides the browser-based UI for submitting inference
jobs and exploring results.

## Tech Stack

- **Next.js 16** with React 19 and TypeScript
- **Mantine 8** — UI component library (forms, tables, modals, badges)
- **`@hey-api/openapi-ts`** — auto-generates a typed API client from the backend's OpenAPI spec

## Features

- Launch genomic inference jobs — pick a model, a HuggingFace dataset path, and optional JSON
  parameters
- Monitor job status with auto-refresh every 5 seconds
- View embedding results in a modal with a CSV preview and download link

## Project Structure

```
apps/web/
├── app/
│   ├── components/
│   │   ├── JobLaunchForm.tsx   # Job submission form
│   │   ├── JobList.tsx         # Jobs table with status badges
│   │   └── ResultsView.tsx     # Embeddings modal / CSV preview
│   ├── lib/
│   │   └── api.ts              # Configures the API client base URL
│   ├── services/backend/       # Auto-generated API client (do not edit)
│   ├── layout.tsx
│   └── page.tsx                # Root page — tabs + polling logic
└── Dockerfile                  # Multi-stage build (Node → Nginx)
```

## Local Development

Run from the repo root (preferred, picks up shared packages via Turborepo):

```bash
npx turbo run dev --filter=web
```

Or directly inside this directory:

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

The API client defaults to `http://localhost:8000`. Override it with the env var:

```bash
NEXT_PUBLIC_API_URL=http://my-backend:8000 npm run dev
```

## Regenerating the Backend API Client

The files under `app/services/backend/` are generated from the backend's OpenAPI spec. Regenerate
them whenever the backend API changes:

```bash
npm run generate-backend-ts-client
```

This reads `apps/backend/build/openapi_spec.json` and writes typed client code to
`app/services/backend/`. Do not edit those files by hand.

## Build & Deployment

### Static export

Next.js is configured with `output: "export"`, which produces a fully static site in `out/`. No
Node.js runtime is required at serve time.

### Docker

The `Dockerfile` uses a two-stage build:

1. **Builder** — installs dependencies and runs `next build` (produces `out/`)
2. **Nginx** — copies `out/` into an `nginx:alpine` image and serves on port 80

Build context must be the **repo root** (the image copies workspace packages):

```bash
docker build -f apps/web/Dockerfile -t helical-workbench-web .
docker run -p 80:80 -e NEXT_PUBLIC_API_URL=http://my-backend:8000 helical-workbench-web
```

> **Important:** `NEXT_PUBLIC_API_URL` is baked into the static assets at build time. Set it before
> running `next build` (or as a Docker build arg / env var passed to the builder stage), not just at
> container runtime.
