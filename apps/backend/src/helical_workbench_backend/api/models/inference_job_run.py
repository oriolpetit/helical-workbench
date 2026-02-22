import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class Model(str, Enum):
    C2S = "c2s"
    GENEFORMER = "geneformer"
    GENEPT = "genept"
    HELIX_MRNA = "helix_mrna"
    HYENA_DNA = "hyena_dna"
    MAMBA2_MRNA = "mamba2_mrna"
    SC_GPT = "scgpt"
    TRANSCRIPTFORMER = "transcriptformer"
    UCE = "uce"


class JobRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class InferenceJobRunInputs(BaseModel):
    data_path: str
    model: Model
    results_path: str | None = None
    parameters: dict[str, Any] = {}


class InferenceJobRunCreate(BaseModel):
    """Request body for POST /inference_job_runs"""

    inputs: InferenceJobRunInputs


class InferenceJobRun(BaseModel):
    """Response schema (also the domain entity)"""

    id: str
    status: JobRunStatus
    inputs: InferenceJobRunInputs
    started_at: datetime.datetime
    finished_at: Optional[datetime.datetime] = None
    result_path: Optional[str] = None
    error: Optional[str] = None
