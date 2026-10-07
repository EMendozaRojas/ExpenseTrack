## 1. Base

- [ ] 1.1 `app/core/openapi.py`: `API_DESCRIPTION`, `Tag` + `OPENAPI_TAGS` (D2), `ErrorResponse`, `error_responses()` y `AUTH_RESPONSES` (D1, D4)
- [ ] 1.2 `app/main.py`: metadatos de la app, tags y `persistAuthorization` (D9); `/health` documentado en Sistema
- [ ] 1.3 `tests/test_openapi_docs.py` según D7 (empieza fallando: sirve de lista de pendientes para el bloque 2)

## 2. Documentar por grupo (endpoints, parámetros, errores y esquemas)

- [ ] 2.1 Autenticación (`routers/auth.py`, `schemas/token.py`, `schemas/user.py`): login, refresh, logout, registro, `me` y Google OAuth (503 sin configurar, 400 `state` inválido, 502/500 si falla Google, redirección)
- [ ] 2.2 Usuario y perfil (`routers/users.py`, `schemas/user.py`): perfil y avatar (subida 413/415, descarga binaria)
- [ ] 2.3 Preferencias (`routers/preferences.py`, `schemas/preferences.py`)
- [ ] 2.4 Cuentas (`routers/accounts.py`, `schemas/account.py`)
- [ ] 2.5 Movimientos (`routers/transactions.py`, `routers/expenses.py`, `schemas/transaction.py`): papelera de 30 días, transferencias, recategorización, disparo de avisos, 400 por cursor inválido; `expenses/summary` en Movimientos (D8)
- [ ] 2.6 Categorías (`routers/categories.py`, `schemas/category.py`): borrado con reasignación y conservación del historial de presupuestos
- [ ] 2.7 Reglas de categorización (`routers/categorization_rules.py`, `schemas/categorization_rule.py`)
- [ ] 2.8 Importación de extractos (`routers/imports.py`, `schemas/imports.py`): formatos, límites 413/415/422, estrategias de commit
- [ ] 2.9 Adjuntos (`routers/attachments.py`, `schemas/attachment.py`): descarga binaria
- [ ] 2.10 Tipos de cambio (`routers/fx_rates.py`, `schemas/fx_rate.py`)
- [ ] 2.11 Presupuestos (`routers/budgets.py`, `schemas/budget.py`): resolución por mes, alcance, meses pasados, copiar, planificados, recomendaciones
- [ ] 2.12 Metas de ahorro (`routers/goals.py`, `schemas/goal.py`)
- [ ] 2.13 Notificaciones (`routers/notifications.py`, `schemas/notification.py`): tipos y revisión al entrar
- [ ] 2.14 Dashboard (`routers/dashboard.py`, `schemas/dashboard.py`)
- [ ] 2.15 Análisis (`routers/insights.py`, `schemas/insights.py`)

## 3. Contrato versionado

- [ ] 3.1 `scripts/export_openapi.py` y `backend/openapi.json` generado (D6)
- [ ] 3.2 `tests/test_openapi_snapshot.py`: falla si el archivo no coincide e indica el comando
- [ ] 3.3 `CLAUDE.md`: cómo regenerar `openapi.json`

## 4. Verificación

- [ ] 4.1 `test_openapi_docs.py` y `test_openapi_snapshot.py` en verde; la suite completa pasa sin cambiar ningún test existente
- [ ] 4.2 `ruff` y `mypy` sin errores nuevos en los archivos tocados; frontend sin cambios (`vitest` en verde)
- [ ] 4.3 Revisión en `/docs` y `/redoc`: introducción, grupos en orden, "Authorize" con el usuario demo y una llamada de prueba a un endpoint protegido
