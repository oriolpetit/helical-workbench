import uvicorn
from fastapi import FastAPI

from helical_workbench_backend.api.router import router

app = FastAPI()
app.include_router(router)


@app.get("/ping")
def read_root() -> dict[str, str]:
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
