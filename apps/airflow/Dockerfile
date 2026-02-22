FROM apache/airflow:3.1.7-python3.10

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN UV_SYSTEM_PYTHON=1 uv sync --frozen --no-dev --no-install-project
