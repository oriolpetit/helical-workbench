# Backend — API

FastAPI backend that bridges the web UI and the Airflow pipeline. Exposes REST endpoints consumed by
`apps/web`.

## Local Development

Uses **uv** for dependency management.

```bash
npm run dev
```

The API will be available at [http://localhost:8000](http://localhost:8000). Interactive docs are
auto-generated at [http://localhost:8000/docs](http://localhost:8000/docs).

## API Endpoints

### Health check

| Method | Path    | Description  |
|--------|---------|--------------|
| GET    | `/ping` | Health check |

### Inference job runs

| Method | Path                                       | Description                                |
|--------|--------------------------------------------|--------------------------------------------|
| GET    | `/inference_job_runs`                      | List all runs (optional `?status=` filter) |
| POST   | `/inference_job_runs`                      | Trigger a new inference job                |
| GET    | `/inference_job_runs/{job_run_id}`         | Get status of a specific job               |
| GET    | `/inference_job_runs/{job_run_id}/results` | Download results CSV                       |

#### POST `/inference_job_runs` — request body

```json
{
  "data_path": "string",
  "model": "string",
  "results_path": "string",
  "parameters": {}
}
```

**Supported models:** `c2s`, `geneformer`, `genept`, `helix_mrna`, `hyena_dna`, `mamba2_mrna`,
`scgpt`, `transcriptformer`, `uce`

#### Response schema (job run object)

```json
{
  "id": "string",
  "status": "string",
  "inputs": {
    "data_path": "string",
    "model": "string",
    "results_path": "string",
    "parameters": {}
  },
  "started_at": "string | null",
  "finished_at": "string | null",
  "result_path": "string | null",
  "error": "string | null"
}
```

**Job statuses:** `pending`, `running`, `succeeded`, `failed`

## OpenAPI Client Generation

The OpenAPI spec is exported from the running FastAPI app and used to auto-generate the TypeScript
client in `apps/web`.

After changing the API (adding/modifying endpoints or schemas), regenerate both:

```bash
# 1. Export the OpenAPI spec (outputs to build/openapi_spec.json)
npm run generate-openapi

# 2. Regenerate the TypeScript client in apps/web
cd ../web && npm run generate-backend-ts-client
```

The generated client lives in `apps/web/app/services/backend/` and should be committed alongside
API changes.

## Testing

```bash
npm run test       # Run pytest suite
```

Uses pytest with pytest-mock. Tests live in `tests/`.

## Code Quality

```bash
npm run type-check   # mypy strict mode
npm run lint         # ruff linting
npm run format       # ruff format + autofix
```

## Configuration

| Environment variable | Description                                          | Default (Docker)                |
|----------------------|------------------------------------------------------|---------------------------------|
| `AIRFLOW_HOST`       | Base URL of the Airflow API server                   | `http://airflow-apiserver:8080` |
| `AIRFLOW_USERNAME`   | Airflow API username                                 | `airflow`                       |
| `AIRFLOW_PASSWORD`   | Airflow API password                                 | `airflow`                       |
| `RESULTS_DIR`        | Directory where inference result files are read from | `/app/results`                  |

Results are shared with the Airflow container via a Docker volume mounted at `apps/airflow/results`.

## Architecture

The app follows a layered design:

```
Routes → Service → Client
```

- **Routes** (`api/routes/`) — HTTP layer, request validation, response serialisation
- **Service** (`services/`) — business logic, job state management
- **Client** (`clients/`) — Airflow REST API integration

The web frontend (`apps/web`) calls this backend. The backend triggers the
`execute_inference_helical_model_dag` Airflow DAG and reads result CSV files from the shared
volume.
