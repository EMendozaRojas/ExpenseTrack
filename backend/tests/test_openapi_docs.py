"""La documentación OpenAPI no puede degradarse (design D7 de api-documentation).

Acumula todos los problemas antes de fallar, para que el mensaje sirva de
lista de lo que falta documentar.
"""

from fastapi.routing import APIRoute

from app.core.openapi import OPENAPI_TAGS
from app.main import app

# Esquemas que genera FastAPI y no se pueden describir campo a campo.
EXEMPT_SCHEMAS = {"HTTPValidationError", "ValidationError"}

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _operation_problems() -> list[str]:
    declared_tags = {tag["name"] for tag in OPENAPI_TAGS}
    described_tags = {tag["name"] for tag in OPENAPI_TAGS if tag.get("description")}
    problems: list[str] = []

    for route in app.routes:
        if isinstance(route, APIRoute) and route.include_in_schema and route.summary is None:
            problems.append(f"{sorted(route.methods)} {route.path}: falta summary explícito")

    for path, operations in app.openapi()["paths"].items():
        for method, operation in operations.items():
            if method not in HTTP_METHODS:
                continue
            name = f"{method.upper()} {path}"
            if not (operation.get("description") or "").strip():
                problems.append(f"{name}: falta descripción")
            tags = operation.get("tags", [])
            if len(tags) != 1 or tags[0] not in declared_tags:
                problems.append(f"{name}: tag no declarado {tags}")
            elif tags[0] not in described_tags:
                problems.append(f"{name}: el tag {tags[0]} no tiene descripción")
            if operation.get("security") and "401" not in operation.get("responses", {}):
                problems.append(f"{name}: requiere autenticación y no documenta 401")
            for parameter in operation.get("parameters", []):
                if not parameter.get("description"):
                    problems.append(
                        f"{name}: el parámetro {parameter['name']} no tiene descripción"
                    )
    return problems


def _schema_problems() -> list[str]:
    problems: list[str] = []
    schemas = app.openapi().get("components", {}).get("schemas", {})
    for schema_name, schema in schemas.items():
        if schema_name in EXEMPT_SCHEMAS:
            continue
        for field_name, field in schema.get("properties", {}).items():
            if not field.get("description"):
                problems.append(f"{schema_name}.{field_name}: falta descripción")
    return problems


def _request_schema_names() -> set[str]:
    names: set[str] = set()
    for operations in app.openapi()["paths"].values():
        for operation in operations.values():
            content = operation.get("requestBody", {}).get("content", {})
            for media in content.values():
                ref = media.get("schema", {}).get("$ref", "")
                if ref:
                    names.add(ref.rsplit("/", 1)[-1])
    return names


def _example_problems() -> list[str]:
    """Los esquemas de entrada llevan un ejemplo en cada campo."""
    problems: list[str] = []
    schemas = app.openapi().get("components", {}).get("schemas", {})
    for schema_name in sorted(_request_schema_names()):
        for field_name, field in schemas[schema_name].get("properties", {}).items():
            # Archivos subidos: OpenAPI 3.0 los marca con `format: binary` y
            # FastAPI >= 0.12x con `contentMediaType`; no llevan ejemplo.
            if field.get("format") == "binary" or "contentMediaType" in field:
                continue
            if not field.get("examples") and "example" not in field:
                problems.append(f"{schema_name}.{field_name}: falta ejemplo")
    return problems


def test_every_operation_is_documented() -> None:
    problems = _operation_problems()
    assert not problems, "Endpoints sin documentar:\n" + "\n".join(problems)


def test_every_schema_field_is_described() -> None:
    problems = _schema_problems()
    assert not problems, "Campos sin descripción:\n" + "\n".join(problems)


def test_request_fields_have_examples() -> None:
    problems = _example_problems()
    assert not problems, "Campos de entrada sin ejemplo:\n" + "\n".join(problems)
