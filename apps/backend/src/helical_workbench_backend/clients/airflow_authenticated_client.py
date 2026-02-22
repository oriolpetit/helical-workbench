from typing import Callable

import requests
from airflow_client.client import ApiClient, Configuration
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AirflowApiConfig(BaseSettings):
    host: str = Field(default="http://localhost:8080", validation_alias="AIRFLOW_HOST")
    username: str = Field(default="airflow", validation_alias="AIRFLOW_USERNAME")
    password: str = Field(default="airflow", validation_alias="AIRFLOW_PASSWORD")

    model_config = {"populate_by_name": True}


class AirflowAccessTokenResponse(BaseModel):
    access_token: str


class AuthnAirflowClient:
    def __init__(
        self,
        api_client_factory: Callable[[Configuration], ApiClient] | None = None,
        airflow_api_config: AirflowApiConfig | None = None,
    ):
        self._api_client_factory = api_client_factory or ApiClient
        self._airflow_api_config = airflow_api_config or AirflowApiConfig()

    def _get_airflow_client_access_token(
        self,
    ) -> str:
        url = f"{self._airflow_api_config.host}/auth/token"
        payload = {
            "username": self._airflow_api_config.username,
            "password": self._airflow_api_config.password,
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 201:
            raise RuntimeError(
                f"Failed to get access token: {response.status_code} {response.text}"
            )
        response_success = AirflowAccessTokenResponse(**response.json())
        return response_success.access_token

    def _get_airflow_configuration(self) -> Configuration:
        return Configuration(
            host=self._airflow_api_config.host,
        )

    def __enter__(self) -> ApiClient:
        configuration = self._get_airflow_configuration()
        configuration.access_token = self._get_airflow_client_access_token()
        return self._api_client_factory(configuration)

    def __exit__(self, exc_type, exc_value, traceback):  # type: ignore[no-untyped-def]
        pass
