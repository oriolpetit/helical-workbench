from fastapi import APIRouter

from helical_workbench_backend.api.routes.inference_job_runs import (
    router as inference_job_runs_router,
)

router = APIRouter()
router.include_router(inference_job_runs_router)
