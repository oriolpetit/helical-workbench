from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from helical_workbench_backend.api.dependencies.airflow import get_batch_processor
from helical_workbench_backend.api.models.inference_job_run import (
    InferenceJobRun,
    InferenceJobRunInputs,
    JobRunStatus,
    Model,
)
from helical_workbench_backend.main import app


@pytest.fixture
def mock_processor():
    return MagicMock()


@pytest.fixture
def client(mock_processor):
    app.dependency_overrides[get_batch_processor] = lambda: mock_processor
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_job_run(**kwargs):
    defaults = dict(
        id="run-123",
        status=JobRunStatus.SUCCEEDED,
        inputs=InferenceJobRunInputs(
            data_path="s3://bucket/data", model=Model.GENEFORMER
        ),
        started_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        result_path="dags/files/output.csv",
        error=None,
    )
    defaults.update(kwargs)
    return InferenceJobRun(**defaults)


class TestListInferenceJobRuns:
    def test_returns_200_with_list(self, client, mock_processor):
        mock_processor.list_dag_runs.return_value = [make_job_run()]
        response = client.get("/inference_job_runs")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1
        assert body[0]["id"] == "run-123"

    def test_passes_status_query_param_to_processor(self, client, mock_processor):
        mock_processor.list_dag_runs.return_value = []
        client.get("/inference_job_runs?status=running")
        mock_processor.list_dag_runs.assert_called_once_with(status="running")

    def test_no_status_param_calls_processor_with_none(self, client, mock_processor):
        mock_processor.list_dag_runs.return_value = []
        client.get("/inference_job_runs")
        mock_processor.list_dag_runs.assert_called_once_with(status=None)

    def test_returns_empty_list(self, client, mock_processor):
        mock_processor.list_dag_runs.return_value = []
        response = client.get("/inference_job_runs")
        assert response.status_code == 200
        assert response.json() == []


class TestCreateInferenceJobRun:
    def test_returns_201_on_success(self, client, mock_processor):
        mock_processor.trigger_dag_run.return_value = make_job_run(
            status=JobRunStatus.PENDING
        )
        payload = {"inputs": {"data_path": "s3://bucket/data", "model": "geneformer"}}
        response = client.post("/inference_job_runs", json=payload)
        assert response.status_code == 201

    def test_response_body_matches_schema(self, client, mock_processor):
        mock_processor.trigger_dag_run.return_value = make_job_run()
        payload = {"inputs": {"data_path": "s3://bucket/data", "model": "geneformer"}}
        response = client.post("/inference_job_runs", json=payload)
        body = response.json()
        assert "id" in body
        assert "status" in body
        assert "inputs" in body

    def test_invalid_model_returns_422(self, client, mock_processor):
        payload = {"inputs": {"data_path": "s3://x", "model": "not_a_real_model"}}
        response = client.post("/inference_job_runs", json=payload)
        assert response.status_code == 422

    def test_missing_data_path_returns_422(self, client, mock_processor):
        payload = {"inputs": {"model": "geneformer"}}
        response = client.post("/inference_job_runs", json=payload)
        assert response.status_code == 422

    def test_all_valid_models_accepted(self, client, mock_processor):
        mock_processor.trigger_dag_run.return_value = make_job_run()
        for model_value in ("geneformer", "scgpt", "helix_mrna"):
            payload = {"inputs": {"data_path": "s3://x", "model": model_value}}
            response = client.post("/inference_job_runs", json=payload)
            assert response.status_code == 201, f"Failed for model: {model_value}"


class TestGetInferenceJobRun:
    def test_returns_200_for_known_run(self, client, mock_processor):
        mock_processor.get_dag_run_status.return_value = make_job_run()
        response = client.get("/inference_job_runs/run-123")
        assert response.status_code == 200
        assert response.json()["id"] == "run-123"

    def test_passes_job_run_id_to_processor(self, client, mock_processor):
        mock_processor.get_dag_run_status.return_value = make_job_run()
        client.get("/inference_job_runs/my-specific-run-id")
        mock_processor.get_dag_run_status.assert_called_once_with("my-specific-run-id")


class TestGetInferenceJobRunResults:
    def test_returns_200_with_file_contents(self, client, mock_processor, tmp_path):
        result_file = tmp_path / "embeddings.csv"
        result_file.write_text("0.1,0.2,0.3")
        mock_processor.get_dag_run_results.return_value = result_file
        response = client.get("/inference_job_runs/run-123/results")
        assert response.status_code == 200

    def test_passes_job_run_id_to_processor(self, client, mock_processor, tmp_path):
        result_file = tmp_path / "embeddings.csv"
        result_file.write_text("0.1,0.2")
        mock_processor.get_dag_run_results.return_value = result_file
        client.get("/inference_job_runs/run-456/results")
        mock_processor.get_dag_run_results.assert_called_once_with("run-456")

    def test_propagates_404_when_processor_raises(self, client, mock_processor):
        from fastapi import HTTPException

        mock_processor.get_dag_run_results.side_effect = HTTPException(
            status_code=404, detail="Results not available yet"
        )
        response = client.get("/inference_job_runs/run-123/results")
        assert response.status_code == 404
