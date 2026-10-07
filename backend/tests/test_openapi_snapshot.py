"""`backend/openapi.json` tiene que coincidir con la API (design D6 de
api-documentation)."""

import json

from app.main import app
from scripts.export_openapi import OPENAPI_PATH, render

REGENERATE = "docker compose exec backend python -m scripts.export_openapi"


def test_openapi_json_is_up_to_date() -> None:
    assert OPENAPI_PATH.exists(), f"Falta {OPENAPI_PATH.name}. Genéralo con: {REGENERATE}"
    committed = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    assert committed == app.openapi(), (
        f"{OPENAPI_PATH.name} no coincide con la API. Regenéralo con: {REGENERATE}"
    )


def test_export_is_stable() -> None:
    assert render(app.openapi()) == render(app.openapi())
