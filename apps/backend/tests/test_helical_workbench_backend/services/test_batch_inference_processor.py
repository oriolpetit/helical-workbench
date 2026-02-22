from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from helical_workbench_backend.api.models.inference_job_run import (
    InferenceJobRun,
    InferenceJobRunCreate,
    InferenceJobRunInputs,
    JobRunStatus,
    Model,
)
from helical_workbench_backend.services.batch_inference_processor import (
    INFERENCE_DAG_ID,
    BatchInferenceProcessorConfig,
    _dag_run_to_job_run,
)


def make_dag_run_response(
    dag_run_id="run-123",
    state="success",
    conf=None,
    start_date=None,
    end_date=None,
    note=None,
):
    """Build a minimal DAGRunResponse-like mock."""
    dag_run = MagicMock()
    dag_run.dag_run_id = dag_run_id
    dag_run.state = state
    dag_run.conf = (
        conf
        if conf is not None
        else {
            "data_path": "s3://bucket/data",
            "model": "geneformer",
            "parameters": {},
        }
    )
    dag_run.start_date = start_date or datetime(2024, 1, 1, tzinfo=timezone.utc)
    dag_run.end_date = end_date
    dag_run.logical_date = dag_run.start_date
    dag_run.note = note
    return dag_run


class TestDagRunToJobRun:
    def test_success_state_sets_result_path(self):
        dag_run = make_dag_run_response(dag_run_id="run-123", state="success")
        inputs = InferenceJobRunInputs(data_path="s3://x", model=Model.GENEFORMER)
        result = _dag_run_to_job_run(dag_run, inputs)
        assert result.status == JobRunStatus.SUCCEEDED
        assert result.result_path == "run-123/embeddings.csv"
        assert result.error is None

    def test_failed_state_sets_error_from_note(self):
        dag_run = make_dag_run_response(state="failed", note="OOM error")
        inputs = InferenceJobRunInputs(data_path="s3://x", model=Model.GENEFORMER)
        result = _dag_run_to_job_run(dag_run, inputs)
        assert result.status == JobRunStatus.FAILED
        assert result.error == "OOM error"
        assert result.result_path is None

    def test_unknown_state_defaults_to_pending(self):
        dag_run = make_dag_run_response(state="deferred")
        inputs = InferenceJobRunInputs(data_path="s3://x", model=Model.GENEFORMER)
        result = _dag_run_to_job_run(dag_run, inputs)
        assert result.status == JobRunStatus.PENDING

    def test_running_state_no_result_path(self):
        dag_run = make_dag_run_response(state="running")
        inputs = InferenceJobRunInputs(data_path="s3://x", model=Model.GENEFORMER)
        result = _dag_run_to_job_run(dag_run, inputs)
        assert result.status == JobRunStatus.RUNNING
        assert result.result_path is None

    def test_returns_inference_job_run_instance(self):
        dag_run = make_dag_run_response()
        inputs = InferenceJobRunInputs(data_path="s3://x", model=Model.GENEFORMER)
        result = _dag_run_to_job_run(dag_run, inputs)
        assert isinstance(result, InferenceJobRun)
        assert result.id == "run-123"


@pytest.fixture
def mock_dag_run_api(mocker):
    mock_api = MagicMock()
    mocker.patch(
        "helical_workbench_backend.services.batch_inference_processor.DagRunApi",
        return_value=mock_api,
    )
    return mock_api


@pytest.fixture
def processor():
    from helical_workbench_backend.services.batch_inference_processor import (
        BatchInferenceProcessor,
    )

    return BatchInferenceProcessor(airflow_client=MagicMock())


class TestTriggerDagRun:
    def test_calls_airflow_with_correct_dag_id(self, processor, mock_dag_run_api):
        mock_dag_run_api.trigger_dag_run.return_value = make_dag_run_response()
        job_create = InferenceJobRunCreate(
            inputs=InferenceJobRunInputs(
                data_path="s3://bucket/data", model=Model.GENEFORMER
            )
        )
        processor.trigger_dag_run(job_create)
        mock_dag_run_api.trigger_dag_run.assert_called_once()
        call_kwargs = mock_dag_run_api.trigger_dag_run.call_args
        assert call_kwargs.kwargs["dag_id"] == INFERENCE_DAG_ID

    def test_dag_run_id_has_api_prefix(self, processor, mock_dag_run_api):
        mock_dag_run_api.trigger_dag_run.return_value = make_dag_run_response()
        job_create = InferenceJobRunCreate(
            inputs=InferenceJobRunInputs(
                data_path="s3://bucket/data", model=Model.GENEFORMER
            )
        )
        processor.trigger_dag_run(job_create)
        body = mock_dag_run_api.trigger_dag_run.call_args.kwargs[
            "trigger_dag_run_post_body"
        ]
        assert body.dag_run_id.startswith("api__")

    def test_conf_contains_inputs(self, processor, mock_dag_run_api):
        mock_dag_run_api.trigger_dag_run.return_value = make_dag_run_response()
        job_create = InferenceJobRunCreate(
            inputs=InferenceJobRunInputs(
                data_path="s3://bucket/data",
                model=Model.GENEFORMER,
                parameters={"lr": 0.01},
            )
        )
        processor.trigger_dag_run(job_create)
        body = mock_dag_run_api.trigger_dag_run.call_args.kwargs[
            "trigger_dag_run_post_body"
        ]
        assert body.conf["data_path"] == "s3://bucket/data"
        assert body.conf["model"] == "geneformer"
        assert body.conf["parameters"] == {"lr": 0.01}

    def test_returns_inference_job_run(self, processor, mock_dag_run_api):
        mock_dag_run_api.trigger_dag_run.return_value = make_dag_run_response(
            state="queued"
        )
        job_create = InferenceJobRunCreate(
            inputs=InferenceJobRunInputs(data_path="s3://x", model=Model.GENEFORMER)
        )
        result = processor.trigger_dag_run(job_create)
        assert isinstance(result, InferenceJobRun)
        assert result.status == JobRunStatus.PENDING


class TestGetDagRunStatus:
    def test_reconstructs_inputs_from_conf(self, processor, mock_dag_run_api):
        dag_run = make_dag_run_response(
            dag_run_id="run-456",
            conf={"data_path": "s3://other", "model": "scgpt", "parameters": {}},
        )
        mock_dag_run_api.get_dag_run.return_value = dag_run
        result = processor.get_dag_run_status("run-456")
        assert result.inputs.data_path == "s3://other"
        assert result.inputs.model == Model.SC_GPT

    def test_calls_get_dag_run_with_correct_ids(self, processor, mock_dag_run_api):
        mock_dag_run_api.get_dag_run.return_value = make_dag_run_response()
        processor.get_dag_run_status("run-789")
        mock_dag_run_api.get_dag_run.assert_called_once_with(
            dag_id=INFERENCE_DAG_ID, dag_run_id="run-789"
        )

    def test_missing_conf_uses_empty_defaults(self, processor, mock_dag_run_api):
        dag_run = make_dag_run_response()
        dag_run.conf = {}
        mock_dag_run_api.get_dag_run.return_value = dag_run
        result = processor.get_dag_run_status("run-123")
        assert result.inputs.data_path == ""


class TestListDagRuns:
    def test_returns_empty_list_when_no_runs(self, processor, mock_dag_run_api):
        mock_dag_run_api.get_dag_runs.return_value.dag_runs = []
        result = processor.list_dag_runs()
        assert result == []

    def test_returns_all_runs_without_filter(self, processor, mock_dag_run_api):
        mock_dag_run_api.get_dag_runs.return_value.dag_runs = [
            make_dag_run_response(dag_run_id="run-1", state="success"),
            make_dag_run_response(dag_run_id="run-2", state="running"),
        ]
        result = processor.list_dag_runs()
        assert len(result) == 2

    def test_passes_status_filter_to_airflow(self, processor, mock_dag_run_api):
        mock_dag_run_api.get_dag_runs.return_value.dag_runs = []
        processor.list_dag_runs(status="running")
        call_kwargs = mock_dag_run_api.get_dag_runs.call_args
        assert call_kwargs.kwargs.get("state") == ["running"]

    def test_no_status_filter_omits_state_kwarg(self, processor, mock_dag_run_api):
        mock_dag_run_api.get_dag_runs.return_value.dag_runs = []
        processor.list_dag_runs(status=None)
        call_kwargs = mock_dag_run_api.get_dag_runs.call_args
        assert "state" not in (call_kwargs.kwargs or {})

    def test_reconstructs_results_path_from_conf(self, processor, mock_dag_run_api):
        dag_run = make_dag_run_response(
            conf={
                "data_path": "s3://x",
                "model": "geneformer",
                "results_path": "run-1/embeddings.csv",
                "parameters": {},
            }
        )
        mock_dag_run_api.get_dag_runs.return_value.dag_runs = [dag_run]
        result = processor.list_dag_runs()
        assert result[0].inputs.results_path == "run-1/embeddings.csv"


class TestTriggerDagRunResultsPath:
    def test_conf_contains_auto_generated_results_path(
        self, processor, mock_dag_run_api
    ):
        mock_dag_run_api.trigger_dag_run.return_value = make_dag_run_response()
        job_create = InferenceJobRunCreate(
            inputs=InferenceJobRunInputs(
                data_path="s3://bucket/data", model=Model.GENEFORMER
            )
        )
        processor.trigger_dag_run(job_create)
        body = mock_dag_run_api.trigger_dag_run.call_args.kwargs[
            "trigger_dag_run_post_body"
        ]
        assert "results_path" in body.conf
        assert body.conf["results_path"].endswith("/embeddings.csv")

    def test_explicit_results_path_is_preserved(self, processor, mock_dag_run_api):
        mock_dag_run_api.trigger_dag_run.return_value = make_dag_run_response()
        job_create = InferenceJobRunCreate(
            inputs=InferenceJobRunInputs(
                data_path="s3://bucket/data",
                model=Model.GENEFORMER,
                results_path="custom/path.csv",
            )
        )
        processor.trigger_dag_run(job_create)
        body = mock_dag_run_api.trigger_dag_run.call_args.kwargs[
            "trigger_dag_run_post_body"
        ]
        assert body.conf["results_path"] == "custom/path.csv"


class TestGetDagRunResults:
    def test_returns_path_when_succeeded_and_file_exists(
        self, mock_dag_run_api, tmp_path
    ):
        from helical_workbench_backend.services.batch_inference_processor import (
            BatchInferenceProcessor,
        )

        result_file = tmp_path / "run-123" / "embeddings.csv"
        result_file.parent.mkdir(parents=True)
        result_file.write_text("1.0,2.0")

        config = BatchInferenceProcessorConfig(results_dir=str(tmp_path))
        processor = BatchInferenceProcessor(airflow_client=MagicMock(), config=config)

        dag_run = make_dag_run_response(dag_run_id="run-123", state="success")
        mock_dag_run_api.get_dag_run.return_value = dag_run

        result = processor.get_dag_run_results("run-123")
        assert result == tmp_path / "run-123" / "embeddings.csv"

    def test_raises_404_when_job_not_succeeded(self, mock_dag_run_api, tmp_path):
        from helical_workbench_backend.services.batch_inference_processor import (
            BatchInferenceProcessor,
        )

        config = BatchInferenceProcessorConfig(results_dir=str(tmp_path))
        processor = BatchInferenceProcessor(airflow_client=MagicMock(), config=config)

        dag_run = make_dag_run_response(dag_run_id="run-123", state="running")
        mock_dag_run_api.get_dag_run.return_value = dag_run

        with pytest.raises(HTTPException) as exc_info:
            processor.get_dag_run_results("run-123")
        assert exc_info.value.status_code == 404

    def test_raises_404_when_file_does_not_exist(self, mock_dag_run_api, tmp_path):
        from helical_workbench_backend.services.batch_inference_processor import (
            BatchInferenceProcessor,
        )

        config = BatchInferenceProcessorConfig(results_dir=str(tmp_path))
        processor = BatchInferenceProcessor(airflow_client=MagicMock(), config=config)

        dag_run = make_dag_run_response(dag_run_id="run-123", state="success")
        mock_dag_run_api.get_dag_run.return_value = dag_run

        with pytest.raises(HTTPException) as exc_info:
            processor.get_dag_run_results("run-123")
        assert exc_info.value.status_code == 404
