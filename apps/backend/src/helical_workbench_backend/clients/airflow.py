import airflow_client.client as airflow
import requests
from airflow_client.client.api.dag_api import DAGApi
from pydantic import BaseModel


class AirflowAccessTokenResponse(BaseModel):
    access_token: str

def get_airflow_client_access_token(
        host: str,
        username: str,
        password: str,
) -> str:
    url = f"{host}/auth/token"
    payload = {
        "username": username,
        "password": password,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        raise RuntimeError(f"Failed to get access token: {response.status_code} {response.text}")
    response_success = AirflowAccessTokenResponse(**response.json())
    return response_success.access_token

def get_airflow_configuration() -> airflow.Configuration:
    return airflow.Configuration(
        host="http://localhost:8080",
    )


def get_dags() -> list[dict]:
    configuration = get_airflow_configuration()
    configuration.access_token = get_airflow_client_access_token(
        host="http://localhost:8080",
        username="airflow",
        password="airflow"
    )
    with airflow.ApiClient(configuration) as api_client:
        dag_api = DAGApi(api_client)
        response = dag_api.get_dags()
        return response.dags
