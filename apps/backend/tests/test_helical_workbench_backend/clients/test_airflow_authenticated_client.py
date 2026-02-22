from unittest.mock import MagicMock, patch

import pytest

from helical_workbench_backend.clients.airflow_authenticated_client import (
    AirflowApiConfig,
    AuthnAirflowClient,
)


@pytest.fixture
def mock_api_client():
    return MagicMock()


@pytest.fixture
def config():
    return AirflowApiConfig(
        host="http://airflow-test:8080",
        username="testuser",
        password="testpass",
    )


def make_token_response(token="test-token", status_code=201):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {"access_token": token}
    mock_resp.text = ""
    return mock_resp


class TestAuthnAirflowClient:
    def test_context_manager_posts_to_auth_token_endpoint(self, config):
        mock_api_client = MagicMock()
        with patch(
            "helical_workbench_backend.clients.airflow_authenticated_client.requests.post"
        ) as mock_post:
            mock_post.return_value = make_token_response()
            client = AuthnAirflowClient(
                api_client_factory=lambda cfg: mock_api_client,
                airflow_api_config=config,
            )
            with client:
                pass
        mock_post.assert_called_once()
        url = mock_post.call_args.args[0]
        assert url == "http://airflow-test:8080/auth/token"

    def test_raises_on_non_201_response(self, config):
        with patch(
            "helical_workbench_backend.clients.airflow_authenticated_client.requests.post"
        ) as mock_post:
            mock_post.return_value = make_token_response(status_code=403)
            client = AuthnAirflowClient(airflow_api_config=config)
            with pytest.raises(RuntimeError, match="Failed to get access token"):
                with client:
                    pass

    def test_injects_access_token_into_configuration(self, config):
        captured = {}

        def capture_factory(cfg):
            captured["cfg"] = cfg
            return MagicMock()

        with patch(
            "helical_workbench_backend.clients.airflow_authenticated_client.requests.post"
        ) as mock_post:
            mock_post.return_value = make_token_response(token="my-bearer-token")
            client = AuthnAirflowClient(
                api_client_factory=capture_factory,
                airflow_api_config=config,
            )
            with client:
                pass
        assert captured["cfg"].access_token == "my-bearer-token"
