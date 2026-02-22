import json
import os

from helical_workbench_backend.main import app

os.makedirs("build", exist_ok=True)
with open("build/openapi_spec.json", "w") as file:
    json.dump(app.openapi(), file)
