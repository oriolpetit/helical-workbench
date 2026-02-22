from fastapi import Depends

from helical_workbench_backend.clients.airflow_authenticated_client import (
    AuthnAirflowClient,
)
from helical_workbench_backend.services.batch_inference_processor import (
    BatchInferenceProcessor,
)


def get_airflow_client() -> AuthnAirflowClient:
    return AuthnAirflowClient()


def get_batch_processor(
    airflow_client: AuthnAirflowClient = Depends(get_airflow_client),
) -> BatchInferenceProcessor:
    return BatchInferenceProcessor(airflow_client=airflow_client)
