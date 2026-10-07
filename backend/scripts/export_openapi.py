"""Regenera `backend/openapi.json`, el contrato OpenAPI versionado de la API.

Ejecutar después de cambiar cualquier endpoint o esquema (el test
`tests/test_openapi_snapshot.py` falla si el archivo no está al día).

Uso:
    docker compose exec backend python -m scripts.export_openapi
"""

import json
from pathlib import Path
from typing import Any

from app.main import app

OPENAPI_PATH = Path(__file__).resolve().parents[1] / "openapi.json"


def render(document: dict[str, Any]) -> str:
    """Formato determinista: FastAPI genera el documento en el orden de
    registro de las rutas, así que no hace falta ordenar las claves."""
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    OPENAPI_PATH.write_text(render(app.openapi()), encoding="utf-8")
    print(f"OpenAPI exportado a {OPENAPI_PATH}")


if __name__ == "__main__":
    main()
