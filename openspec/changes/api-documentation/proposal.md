## Why

FastAPI genera la documentación de la API en `/docs` y `/redoc`, pero hoy está casi vacía. De 74 endpoints, solo 1 tiene descripción. Ninguno de los 327 campos de los 69 esquemas está explicado. Los títulos salen del nombre de la función, en inglés ("List Budgets"). No se documentan los errores y la API no tiene introducción. Quien la use, incluido el propio frontend o quien revise el proyecto como portafolio, tiene que leer el código para saber, por ejemplo, que `period` va en formato `YYYY-MM`, que los gastos son importes negativos o cuándo un presupuesto responde 409. Ahora que hay reglas de negocio no obvias (presupuestos por mes con alcance, papelera, importación con estrategias), la documentación tiene que explicarlas y no degradarse con el tiempo.

## What Changes

- **Introducción general** de la API en español: qué es, cómo autenticarse (login con email/contraseña o Google, token de acceso, refresh, botón "Authorize" de Swagger), convenciones (importes decimales como texto, signo de los gastos, fechas y meses `YYYY-MM`, aislamiento por usuario) y formato de los errores.
- **Grupos (tags) en español con descripción**: Autenticación, Usuario y perfil, Preferencias, Cuentas, Movimientos, Categorías, Reglas de categorización, Importación de extractos, Adjuntos, Tipos de cambio, Presupuestos, Metas de ahorro, Notificaciones, Dashboard, Análisis y Sistema.
- **Cada endpoint** con título en español y una descripción de qué hace y de sus reglas de negocio.
- **Errores documentados** por endpoint (400, 401, 404, 409, 413, 415, 422, 500, 502, 503 según corresponda) con un esquema de error común y ejemplos.
- **Campos** de los esquemas, parámetros de ruta y de consulta con descripción y, en las entradas, ejemplo.
- **`openapi.json` versionado** en el repo (`backend/openapi.json`), con un script que lo regenera y un test que falla si no coincide con la API.
- **Test de completitud**: falla si un endpoint o un campo queda sin documentar.
- `GET /expenses/summary` se documenta dentro de **Movimientos**, sin cambiar la ruta, y `/health` dentro de **Sistema**.
- Sin cambios de comportamiento: rutas, parámetros, cuerpos, respuestas y mensajes de error quedan igual.

### Fuera de alcance

- Unificar `GET /expenses/summary` con `GET /dashboard/summary` (renombrar o eliminar): se anota como mejora futura en el design (D8).
- Traducir los mensajes de error, que ya están en español, o cambiar su formato.
- Generar los tipos del frontend desde `openapi.json`: el archivo lo permitirá en el futuro, pero no se hace aquí.
- Arreglar los errores previos de `ruff`, `mypy`, `eslint` y Prettier ajenos a los archivos que toque este change.

## Capabilities

### New Capabilities

- `api-documentation`: documentación OpenAPI completa en español de la API REST, con introducción, grupos, endpoints, errores y campos descritos, contrato `openapi.json` versionado y tests que impiden que se degrade.

### Modified Capabilities

(ninguna: no cambia el comportamiento de ningún endpoint)

## Impact

- **Backend**: nuevo `app/core/openapi.py` (introducción, tags, esquema de error común y ayudas para declarar errores); `app/main.py` (metadatos de la app y opciones de Swagger UI); todos los routers de `app/routers/` (títulos, descripciones, errores, tags y parámetros); todos los esquemas de `app/schemas/` (descripción y ejemplos de los campos); nuevo `scripts/export_openapi.py`; nuevo `backend/openapi.json`; nuevos tests `tests/test_openapi_docs.py` (completitud) y `tests/test_openapi_snapshot.py` (sincronía).
- **Frontend**: sin cambios (los tags no afectan al cliente; `operationId` y rutas no cambian).
- **Documentación del proyecto**: `CLAUDE.md` explica cómo regenerar `openapi.json`.
- **Infra / dependencias**: sin cambios.
