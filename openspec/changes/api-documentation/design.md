## Context

Ver `proposal.md` — Why. Estado actual (2026-10-07):

- `app/main.py` crea `FastAPI(title="ExpenseTrack API")` sin descripción, sin `openapi_tags` y con la versión por defecto (`0.1.0`). Incluye 16 routers con `prefix="/api/v1"` y `/health` sin tag.
- Los routers usan tags en inglés y en minúsculas (`budgets`, `fx-rates`…). Los títulos de los endpoints los genera FastAPI a partir del nombre de la función. Solo `POST /notifications/check` tiene docstring.
- Errores: no hay manejador propio. `HTTPException` responde `{"detail": "<mensaje en español>"}`, y los errores de validación (422) responden `{"detail": [{"loc", "msg", "type"}]}`. Si falta el token, `OAuth2PasswordBearer` responde 401 con el mensaje propio de FastAPI (`"Not authenticated"`); si el token no es válido, responde 401 con `"No se pudieron validar las credenciales"`. Códigos usados: 400, 401, 404, 409, 413, 415, 422, 500, 502 y 503.
- Respuestas que no son JSON: descarga de adjuntos y del avatar (fichero binario) y el inicio del login con Google (redirección).
- Los esquemas Pydantic de `app/schemas/` no tienen `Field(description=...)` en ningún campo.

Decisiones tomadas con el usuario (2026-10-07): todo en español, los 6 puntos (introducción, tags, endpoints, errores, campos con ejemplos y test de completitud), `openapi.json` versionado con test de sincronía, y `expenses/summary` documentado dentro de Movimientos sin cambiar la ruta.

## Goals / Non-Goals

**Goals:**
- Que `/docs` sirva para usar la API sin leer el código.
- Que la documentación no se degrade: los tests fallan si falta.
- Que el contrato quede visible en el repo (`openapi.json`).
- Cero cambios de comportamiento.

**Non-Goals:**
- Cambiar rutas, códigos de estado, mensajes o formato de error.
- Unificar `expenses/summary` con `dashboard/summary` (D8).
- Generar tipos del frontend desde `openapi.json`.
- Documentación fuera de OpenAPI (guías, sitio estático).

## Decisions

### D1 — Un módulo central `app/core/openapi.py`
Concentra lo que no pertenece a un router concreto:
- `API_DESCRIPTION`: la introducción en Markdown (autenticación, convenciones, errores).
- `class Tag(StrEnum)` con los 16 grupos en español y `OPENAPI_TAGS`, la lista con su descripción, que se pasa a `FastAPI(openapi_tags=...)`. Los routers usan `tags=[Tag.PRESUPUESTOS]`, así un tag mal escrito no compila en lugar de crear un grupo nuevo.
- `ErrorResponse(BaseModel)`: `detail: str` con descripción y ejemplo.
- `error_responses(*codes, **overrides)`: devuelve el dict `responses=` de FastAPI con `ErrorResponse`, una descripción por defecto para cada código y un ejemplo; `overrides` permite una descripción específica del endpoint (por ejemplo `{409: "Ya existe un presupuesto para esta categoría en este mes, o el mes es pasado"}`).
- `AUTH_RESPONSES = error_responses(401)` se declara a nivel de `APIRouter(responses=...)` en todos los routers protegidos, y no endpoint a endpoint.

Alternativa descartada: personalizar el documento con `app.openapi()` post-procesado. Separa la documentación del código que describe y es más difícil de mantener.

### D2 — Nombres de los grupos
| Tag actual | Grupo |
|---|---|
| `auth` | Autenticación |
| `users` | Usuario y perfil |
| `preferences` | Preferencias |
| `accounts` | Cuentas |
| `transactions`, `expenses` | Movimientos |
| `categories` | Categorías |
| `categorization-rules` | Reglas de categorización |
| `imports` | Importación de extractos |
| `attachments` | Adjuntos |
| `fx-rates` | Tipos de cambio |
| `budgets` | Presupuestos |
| `goals` | Metas de ahorro |
| `notifications` | Notificaciones |
| `dashboard` | Dashboard |
| `insights` | Análisis |
| (sin tag) `/health` | Sistema |

El orden de `OPENAPI_TAGS` es el de la tabla (flujo natural: entrar, configurar, registrar, planificar, analizar). Cambiar el nombre del tag no afecta al `operationId` (FastAPI lo deriva del nombre de la función y la ruta), así que el frontend no se entera.

### D3 — Endpoints: `summary` en el decorador, descripción en el docstring
- `summary="Crear presupuesto"` en el decorador: título corto, en infinitivo.
- La descripción es el docstring de la función, en Markdown: qué hace, reglas de negocio y efectos secundarios (por ejemplo, "dispara la revisión de avisos de presupuesto"). FastAPI lo usa como `description`. Queda junto al código y se lee bien también en el editor.
- Parámetros de ruta y de consulta: `Path(description=..., examples=[...])` / `Query(...)`. Para `year`/`month`/`period` se reutilizan alias `Annotated` comunes donde ya existen (como en `routers/budgets.py`).
- Respuestas no JSON: `response_class=` y `responses={200: {"content": {"<media-type>": {}}, "description": ...}}` para descargas; `307` documentado para la redirección de Google.

### D4 — Errores
- Cada endpoint declara `responses=error_responses(...)` con los códigos que puede devolver además del 401 del router. Los 422 de validación los añade FastAPI automáticamente cuando hay parámetros o cuerpo. Se declaran a mano solo los 422 que lanza el propio código (por ejemplo, CSV con columnas no reconocidas), con `ErrorResponse`.
- El 401 del router describe los dos casos (falta el token → `"Not authenticated"`; token inválido o caducado → `"No se pudieron validar las credenciales"`). No se traduce el mensaje de FastAPI: sería un cambio de comportamiento.
- Para no olvidar códigos, al documentar cada router se revisan sus `HTTPException` y las de los servicios que llama (por ejemplo, `BudgetError` en `budget_operations`).

### D5 — Campos: `Field(description=..., examples=[...])`
- Todos los campos de `app/schemas/` llevan `description`; los de entrada (`*Create`, `*Update`, `*Input`, `*Request`) llevan además `examples`.
- Los cuerpos de formulario (login con `OAuth2PasswordRequestForm`, subidas con `File`/`Form`) generan esquemas `Body_*`: se documentan con `Form(description=...)` / `File(description=...)`. `OAuth2PasswordRequestForm` no se puede describir campo a campo sin reemplazarlo: se sustituye por parámetros `Form` equivalentes (`username`, `password`) solo si el esquema no cambia de forma; si no, se añade a la lista de exentos del test (D7) con un comentario.
- Validadores, tipos y valores por defecto no cambian.

### D6 — `openapi.json` versionado
- Ruta: `backend/openapi.json`, junto al código que lo genera. Como el contenedor del backend solo monta carpetas concretas (`app`, `tests`, `scripts`…), se añade a `docker-compose.yml` el montaje `./backend/openapi.json:/app/openapi.json` para que el script lo escriba en el repo y el test lo lea. (Ajuste descubierto al implementar, 2026-10-07.)
- `scripts/export_openapi.py` escribe `json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"`. Es determinista porque FastAPI construye el documento en el orden de registro de las rutas. Se ejecuta con `docker compose exec backend python -m scripts.export_openapi`.
- `tests/test_openapi_snapshot.py` compara el archivo con `app.openapi()` (como objetos, no como texto) y, si difieren, falla indicando el comando para regenerarlo.
- `CLAUDE.md` añade el comando en "Cómo se corren los tests" o en una sección propia.

### D7 — Test de completitud `tests/test_openapi_docs.py`
Recorre `app.openapi()` y acumula todos los problemas antes de fallar (mensaje con la lista completa):
- cada operación tiene `summary` explícito (se comprueba en `app.routes` que `route.summary` no es `None`, porque el documento siempre trae un `summary` autogenerado) y `description` no vacía;
- cada operación tiene exactamente un tag, y está en `OPENAPI_TAGS`;
- toda operación con `security` documenta `401`;
- cada propiedad de cada esquema de `components.schemas` tiene `description`, salvo los exentos: `HTTPValidationError`, `ValidationError` y los que se listen explícitamente con su motivo.

### D8 — `GET /expenses/summary`
- Se mueve al tag Movimientos y se documenta como "Resumen mensual de gastos por categoría (lista plana)". La ruta y el router (`routers/expenses.py`) no cambian.
- La descripción indica que el dashboard (`GET /dashboard/summary`) ofrece un resumen más completo y en árbol.
- **Mejora futura** (fuera de este change): unificarlo, renombrándolo a `/transactions/summary` o haciendo que Movimientos use `GET /dashboard/summary` y eliminándolo. Necesitaría un change propio porque rompe el contrato.

### D9 — Metadatos de la app
- `FastAPI(title="ExpenseTrack API", version="0.1.0", description=API_DESCRIPTION, openapi_tags=OPENAPI_TAGS, swagger_ui_parameters={"persistAuthorization": True})`. La versión se mantiene en `0.1.0` (la de `pyproject.toml`); subirla es una decisión aparte.

## Risks / Trade-offs

- [Mucho volumen: 74 endpoints y 327 campos] → las tareas se dividen por grupo, y el test de completitud indica exactamente qué falta.
- [La documentación puede no coincidir con el comportamiento] → las descripciones se escriben leyendo el código y los tests de cada router; los errores, revisando sus `HTTPException`. La suite actual debe seguir pasando sin cambios.
- [`openapi.json` genera ruido en los diffs] → es intencionado: cada cambio de contrato queda visible en la revisión.
- [Un `Field(examples=...)` mal tipado podría cambiar la validación] → `examples` es solo metadato en Pydantic v2; no se tocan `default`, `ge`/`le` ni validadores.

## Migration Plan

Sin migraciones. Despliegue: con `docker compose up` el backend sirve la nueva documentación; nada que migrar en el frontend.

## Open Questions

(ninguna)
