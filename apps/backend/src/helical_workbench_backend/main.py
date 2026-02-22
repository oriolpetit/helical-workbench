import uvicorn
from fastapi import FastAPI

from helical_workbench_backend.clients.airflow import get_dags

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/dags")
def list_dags():
    return get_dags()


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
