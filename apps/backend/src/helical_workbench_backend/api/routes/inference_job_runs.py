from typing import Optional

from fastapi import APIRouter, Depends

from helical_workbench_backend.api.dependencies.airflow import get_batch_processor
from helical_workbench_backend.api.models.inference_job_run import (
    InferenceJobRun,
    InferenceJobRunCreate,
)
from helical_workbench_backend.services.batch_inference_processor import (
    BatchInferenceProcessor,
)

router = APIRouter(prefix="/inference_job_runs", tags=["inference_job_runs"])


@router.get("", response_model=list[InferenceJobRun])
def list_inference_job_runs(
    status: Optional[str] = None,
    processor: BatchInferenceProcessor = Depends(get_batch_processor),
) -> list[InferenceJobRun]:
    return processor.list_dag_runs(status=status)


@router.post("", response_model=InferenceJobRun, status_code=201)
def create_inference_job_run(
    job_create: InferenceJobRunCreate,
    processor: BatchInferenceProcessor = Depends(get_batch_processor),
) -> InferenceJobRun:
    return processor.trigger_dag_run(job_create)


@router.get("/{job_run_id}", response_model=InferenceJobRun)
def get_inference_job_run(
    job_run_id: str,
    processor: BatchInferenceProcessor = Depends(get_batch_processor),
) -> InferenceJobRun:
    return processor.get_dag_run_status(job_run_id)
