import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from airflow_client.client import DAGRunResponse, TriggerDAGRunPostBody
from airflow_client.client.api.dag_run_api import DagRunApi
from fastapi import HTTPException
from pydantic import Field
from pydantic_settings import BaseSettings

from helical_workbench_backend.api.models.inference_job_run import (
    InferenceJobRun,
    InferenceJobRunCreate,
    InferenceJobRunInputs,
    JobRunStatus,
)
from helical_workbench_backend.clients.airflow_authenticated_client import (
    AuthnAirflowClient,
)

INFERENCE_DAG_ID = "execute_inference_helical_model_dag"

_AIRFLOW_STATE_MAP = {
    "queued": JobRunStatus.PENDING,
    "running": JobRunStatus.RUNNING,
    "success": JobRunStatus.SUCCEEDED,
    "failed": JobRunStatus.FAILED,
}


class BatchInferenceProcessorConfig(BaseSettings):
    results_dir: str = Field(
        default="./../airflow/results", validation_alias="RESULTS_DIR"
    )
    model_config = {"populate_by_name": True}


def _dag_run_to_job_run(
    dag_run: DAGRunResponse, inputs: InferenceJobRunInputs
) -> InferenceJobRun:
    state = _AIRFLOW_STATE_MAP.get(dag_run.state, JobRunStatus.PENDING)
    return InferenceJobRun(
        id=dag_run.dag_run_id,
        status=state,
        inputs=inputs,
        started_at=dag_run.start_date
        or dag_run.logical_date
        or datetime.now(timezone.utc),
        finished_at=dag_run.end_date,
        result_path=f"{dag_run.dag_run_id}/embeddings.csv"
        if state == JobRunStatus.SUCCEEDED
        else None,
        error=dag_run.note if state == JobRunStatus.FAILED else None,
    )


class BatchInferenceProcessor:
    def __init__(
        self,
        airflow_client: AuthnAirflowClient,
        config: BatchInferenceProcessorConfig | None = None,
    ):
        self._airflow_client = airflow_client
        self._config = config or BatchInferenceProcessorConfig()

    def trigger_dag_run(self, job_create: InferenceJobRunCreate) -> InferenceJobRun:
        dag_run_id = f"api__{uuid.uuid4()}"
        job_create.inputs.results_path = (
            job_create.inputs.results_path or f"{dag_run_id}/embeddings.csv"
        )
        with self._airflow_client as api_client:
            dag_run_api = DagRunApi(api_client)
            dag_run = dag_run_api.trigger_dag_run(
                dag_id=INFERENCE_DAG_ID,
                trigger_dag_run_post_body=TriggerDAGRunPostBody(
                    dag_run_id=dag_run_id,
                    logical_date=datetime.now(timezone.utc),
                    conf=job_create.inputs.model_dump(),
                ),
            )
        return _dag_run_to_job_run(dag_run, job_create.inputs)

    def get_dag_run_status(self, dag_run_id: str) -> InferenceJobRun:
        with self._airflow_client as api_client:
            dag_run_api = DagRunApi(api_client)
            dag_run = dag_run_api.get_dag_run(
                dag_id=INFERENCE_DAG_ID, dag_run_id=dag_run_id
            )
        # Reconstruct inputs from DAG run conf
        conf = dag_run.conf or {}
        inputs = InferenceJobRunInputs(
            data_path=conf.get("data_path", ""),
            model=conf.get("model", "geneformer"),
            results_path=conf.get("results_path"),
            parameters=conf.get("parameters", {}),
        )
        return _dag_run_to_job_run(dag_run, inputs)

    def list_dag_runs(self, status: str | None = None) -> list[InferenceJobRun]:
        with self._airflow_client as api_client:
            dag_run_api = DagRunApi(api_client)
            kwargs: dict[str, Any] = {}
            if status:
                kwargs["state"] = [status]
            response = dag_run_api.get_dag_runs(dag_id=INFERENCE_DAG_ID, **kwargs)
        runs = response.dag_runs or []
        result = []
        for dag_run in runs:
            conf = dag_run.conf or {}
            inputs = InferenceJobRunInputs(
                data_path=conf.get("data_path", ""),
                model=conf.get("model", "geneformer"),
                results_path=conf.get("results_path"),
                parameters=conf.get("parameters", {}),
            )
            result.append(_dag_run_to_job_run(dag_run, inputs))
        return sorted(result, key=lambda r: r.started_at, reverse=True)

    def get_dag_run_results(self, dag_run_id: str) -> Path:
        status = self.get_dag_run_status(dag_run_id)
        if status.status != JobRunStatus.SUCCEEDED:
            raise HTTPException(status_code=404, detail="Results not available yet")
        full_result_path = Path(self._config.results_dir) / Path(
            status.result_path or ""
        )
        if full_result_path.exists() and full_result_path.is_file():
            return full_result_path
        else:
            raise HTTPException(status_code=404, detail="Results not available")
