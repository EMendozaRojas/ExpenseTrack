"""Metadatos de la documentación OpenAPI (`/docs`, `/redoc`, `openapi.json`).

Concentra lo que no pertenece a un router concreto: la introducción de la
API, los grupos (tags) y el esquema común de error con las ayudas para
declarar los errores de cada endpoint.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

API_TITLE = "ExpenseTrack API"
API_VERSION = "0.1.0"

API_DESCRIPTION = """
API REST de **ExpenseTrack**, una aplicación de finanzas personales: cuentas,
movimientos, categorías con reglas de categorización automática,
presupuestos mensuales, metas de ahorro, varias monedas, adjuntos de recibos,
importación de extractos bancarios en CSV, notificaciones y análisis del gasto.

## Autenticación

1. Crea una cuenta con `POST /api/v1/auth/register`, o entra con Google
   (`GET /api/v1/auth/oauth/google/start`).
2. Inicia sesión con `POST /api/v1/auth/login` (formulario `username` = email,
   `password`). La respuesta trae un `access_token` de corta duración y un
   `refresh_token`.
3. Envía el token en cada petición: `Authorization: Bearer <access_token>`.
4. Cuando caduque, pide uno nuevo con `POST /api/v1/auth/refresh`. Para
   cerrar sesión, revoca el refresh token con `POST /api/v1/auth/logout`.

En esta página, el botón **Authorize** hace el login por ti: escribe tu email
en `username` y tu contraseña. La autorización se conserva al recargar.

## Convenciones

- **Importes**: decimales serializados como texto (`"123.45"`) para no perder
  precisión. En los movimientos, los **gastos son negativos** y los ingresos
  positivos. Los presupuestos, metas y totales de gasto se expresan en
  positivo.
- **Fechas** en formato ISO 8601 (`2026-10-07`); fechas y horas con zona
  horaria. Los **meses** se indican con `year` y `month` o como `YYYY-MM`
  (`2026-10`).
- **Aislamiento**: cada usuario solo ve y modifica sus propios datos. Pedir un
  recurso de otro usuario responde `404`, igual que si no existiera.
- **Moneda**: cada usuario tiene una moneda base (`base_currency` en
  preferencias). Los movimientos en otra moneda guardan el tipo de cambio.

## Errores

Los errores responden con un cuerpo JSON `{"detail": "<mensaje>"}`, con el
mensaje en español. Los errores de validación de la petición (`422`) devuelven
en `detail` una lista con la ubicación (`loc`), el mensaje (`msg`) y el tipo
(`type`) de cada problema. Sin token, o con un token inválido o caducado, la
respuesta es `401`.
"""


class Tag(StrEnum):
    """Grupos de la documentación, en el orden en que se muestran."""

    AUTENTICACION = "Autenticación"
    USUARIO = "Usuario y perfil"
    PREFERENCIAS = "Preferencias"
    CUENTAS = "Cuentas"
    MOVIMIENTOS = "Movimientos"
    CATEGORIAS = "Categorías"
    REGLAS = "Reglas de categorización"
    IMPORTACION = "Importación de extractos"
    ADJUNTOS = "Adjuntos"
    TIPOS_DE_CAMBIO = "Tipos de cambio"
    PRESUPUESTOS = "Presupuestos"
    METAS = "Metas de ahorro"
    NOTIFICACIONES = "Notificaciones"
    DASHBOARD = "Dashboard"
    ANALISIS = "Análisis"
    SISTEMA = "Sistema"


_TAG_DESCRIPTIONS: dict[Tag, str] = {
    Tag.AUTENTICACION: "Registro, login con email y contraseña o con Google, renovación del "
    "token de acceso y cierre de sesión.",
    Tag.USUARIO: "Datos del usuario autenticado: nombre y foto de perfil.",
    Tag.PREFERENCIAS: "Preferencias del usuario: moneda base e idioma.",
    Tag.CUENTAS: "Cuentas donde se registran los movimientos (efectivo, cuenta corriente, "
    "tarjeta…), con su saldo y su moneda.",
    Tag.MOVIMIENTOS: "Ingresos, gastos y transferencias entre cuentas: alta, edición, "
    "papelera de 30 días, recategorización en bloque y resumen mensual de gastos.",
    Tag.CATEGORIAS: "Categorías de dos niveles (raíz y subcategoría). Las de sistema son "
    "comunes a todos los usuarios; cada usuario puede crear las suyas.",
    Tag.REGLAS: "Reglas que asignan automáticamente una categoría a los movimientos según "
    "su descripción.",
    Tag.IMPORTACION: "Importación de extractos bancarios en CSV: vista previa con detección "
    "de duplicados y confirmación con una estrategia.",
    Tag.ADJUNTOS: "Recibos y documentos adjuntos a un movimiento.",
    Tag.TIPOS_DE_CAMBIO: "Tipos de cambio entre monedas usados para los movimientos en una "
    "moneda distinta a la de la cuenta.",
    Tag.PRESUPUESTOS: "Presupuestos mensuales por categoría: monto propio en cada mes, "
    "repetición, edición con alcance, meses pasados de solo lectura, ritmo de gasto y "
    "recomendaciones a partir del historial.",
    Tag.METAS: "Metas de ahorro con aportaciones, progreso y proyección de la fecha en que "
    "se alcanzarán.",
    Tag.NOTIFICACIONES: "Avisos de presupuestos y metas, resumen de cierre de mes y revisión "
    "de avisos al entrar a la app.",
    Tag.DASHBOARD: "Resumen del mes para la pantalla principal: ingresos, gastos, neto, "
    "gastos fijos y variables y gasto por categoría.",
    Tag.ANALISIS: "Análisis del gasto: gastos recurrentes y gasto hormiga, con sus ajustes.",
    Tag.SISTEMA: "Estado del servicio.",
}

OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": tag.value, "description": _TAG_DESCRIPTIONS[tag]} for tag in Tag
]


class ErrorResponse(BaseModel):
    """Cuerpo de los errores que devuelve la API."""

    detail: str = Field(
        description="Mensaje del error, en español.",
        examples=["Presupuesto no encontrado"],
    )


_DEFAULT_ERROR_DESCRIPTIONS: dict[int, str] = {
    400: "Petición incorrecta.",
    401: "Falta el token de acceso (`Not authenticated`) o no es válido o ha caducado "
    "(`No se pudieron validar las credenciales`).",
    404: "El recurso no existe o pertenece a otro usuario.",
    409: "La operación entra en conflicto con el estado actual.",
    413: "El archivo supera el tamaño máximo permitido.",
    415: "Tipo de archivo no admitido.",
    422: "Los datos no son válidos.",
    500: "Error interno.",
    502: "El servicio externo respondió con un error.",
    503: "El servicio no está disponible o no está configurado.",
}

_DEFAULT_ERROR_EXAMPLES: dict[int, str] = {
    400: "Petición incorrecta",
    401: "No se pudieron validar las credenciales",
    404: "Recurso no encontrado",
    409: "Conflicto con el estado actual",
    413: "El archivo supera el tamaño máximo",
    415: "Tipo de archivo no admitido",
    422: "Los datos no son válidos",
    500: "Error interno",
    502: "Error del servicio externo",
    503: "Servicio no disponible",
}


def error_responses(
    *codes: int, **overrides: str | tuple[str, str]
) -> dict[int | str, dict[str, Any]]:
    """`responses=` de FastAPI para los códigos de error de un endpoint.

    Cada código usa `ErrorResponse` con una descripción y un ejemplo por
    defecto. `overrides` (claves `e404`, `e409`…) da una descripción propia
    del endpoint, o una tupla `(descripción, ejemplo de detail)`.
    """
    responses: dict[int | str, dict[str, Any]] = {}
    for code in codes:
        description = _DEFAULT_ERROR_DESCRIPTIONS[code]
        example = _DEFAULT_ERROR_EXAMPLES[code]
        override = overrides.get(f"e{code}")
        if isinstance(override, tuple):
            description, example = override
        elif override is not None:
            description = override
        responses[code] = {
            "model": ErrorResponse,
            "description": description,
            "content": {"application/json": {"example": {"detail": example}}},
        }
    return responses


AUTH_RESPONSES = error_responses(401)
