# Airflow — Inference Pipeline

Apache Airflow 3 pipeline that runs [Helical](https://github.com/helical-ai/helical) genomic model
inference. Uses CeleryExecutor with Redis as broker and PostgreSQL as backend.

## System Requirements

The `airflow-init` service checks these at startup and will warn if they are not met:

- RAM ≥ 4 GB
- CPUs ≥ 2
- Disk ≥ 10 GB

## Docker

The Airflow stack is started as part of the root `docker compose up --build`. The UI is available
at [http://localhost:8080](http://localhost:8080) (credentials: `airflow` / `airflow`).

### Services

| Service                 | Image              | Description              |
|-------------------------|--------------------|--------------------------|
| `postgres`              | postgres:16        | Metadata database        |
| `redis`                 | redis:7.2-bookworm | Celery broker            |
| `airflow-apiserver`     | custom             | Web UI on port 8080      |
| `airflow-scheduler`     | custom             | DAG scheduling           |
| `airflow-dag-processor` | custom             | DAG file parsing         |
| `airflow-worker`        | custom             | Celery task execution    |
| `airflow-triggerer`     | custom             | Deferred task triggering |

## DAGs

DAGs live in `dags/`. The primary DAG (`execute_inference_helical_model_dag`) runs Helical genomic
model inference on HuggingFace datasets and writes embeddings as CSV.

Heavy imports (torch, helical, datasets) are done inside task functions to avoid DAG parse-time
overhead.

### DAG Parameters

Set these in the Airflow UI (Trigger DAG w/ config) or via the CLI:

| Parameter      | Default                    | Description                                |
|----------------|----------------------------|--------------------------------------------|
| `data_path`    | `helical-ai/yolksac_human` | HuggingFace dataset path                   |
| `model_name`   | `geneformer`               | Model to run (see supported models below)  |
| `results_path` | *(auto: run ID)*           | Override output filename                   |
| `parameters`   | `{}`                       | Model-specific kwargs passed to the config |

### Supported Models

| Model name         | Class            |
|--------------------|------------------|
| `c2s`              | Cell2Sen         |
| `geneformer`       | Geneformer       |
| `genept`           | GenePT           |
| `helix_mrna`       | HelixmRNA        |
| `hyena_dna`        | HyenaDNA         |
| `mamba2_mrna`      | Mamba2mRNA       |
| `scgpt`            | scGPT            |
| `transcriptformer` | TranscriptFormer |
| `uce`              | UCE              |

## Output

Embeddings are written as CSV to `./results/<run_id>.csv` on the host (volume-mounted from
`/opt/airflow/results/` inside the containers). If `results_path` is set, that value is used as the
filename instead of the run ID.

## Local Development

Uses **uv** for dependency management. Python version is pinned in `.python-version`.

```bash
uv sync
uv run python main.py
```

## Adding Python Dependencies

- **Docker image** — edit `requirements.txt` (generated from `pyproject.toml` via `uv export`) and
  rebuild the image with `docker compose up --build`
- **Local dev** — edit `pyproject.toml` and run `uv sync`
