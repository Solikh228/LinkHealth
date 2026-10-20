import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from app.main import app
except ImportError:
    from backend.app.main import app

import yaml

def export_openapi():
    spec = app.openapi()

    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "openapi.yaml"))
    with open(backend_path, "w", encoding="utf-8") as f:
        yaml.dump(spec, f, sort_keys=False, allow_unicode=True)
    print(f"Exported OpenAPI spec to: {backend_path}")

    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "openapi.yaml"))
    with open(root_path, "w", encoding="utf-8") as f:
        yaml.dump(spec, f, sort_keys=False, allow_unicode=True)
    print(f"Exported OpenAPI spec to: {root_path}")

if __name__ == "__main__":
    export_openapi()
