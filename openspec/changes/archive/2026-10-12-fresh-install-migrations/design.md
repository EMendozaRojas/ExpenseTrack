## Context

- `fac793ec36d3` (2026-09-04) siembra la taxonomía original llamando a `seed_plan()` y `SYSTEM_RULES` de `app/db/seed_categories.py`. En `a4203f2` (2026-09-09) ese módulo pasó a la taxonomía v2 y las subcategorías de `str` a `SeedSub`, así que la migración antigua inserta datos que no son los suyos y falla al pasar un `SeedSub` como `:name`.
- `b5963a0e5c7c` (taxonomía v2) importa `EXPENSE_ROOTS`, `LEGACY_SUBCATEGORY_MAP`, `SYSTEM_RULES` y `UNCATEGORIZED_EXPENSE`. Hoy funciona porque el módulo no ha cambiado desde entonces, pero se rompería en cuanto alguien edite el seed.
- El backend arranca con `uvicorn` directamente; `alembic.ini` no fija `sqlalchemy.url` y `env.py` la toma siempre de `DATABASE_URL`.

## Goals / Non-Goals

**Goals:** `cp .env.example .env && docker compose up --build` deja la app usable sin pasos extra; las migraciones no dependen de código que cambia; un test lo vigila.

**Non-Goals:** aislar el resto de tests de la base de desarrollo (change `test-isolation`); CI (change `quality-and-dependencies`); cambiar la taxonomía.

## Decisions

### D1 — Congelar los datos dentro de cada migración
- `fac793ec36d3`: se copian literalmente `EXPENSE_ROOTS`, `INCOME_ROOTS`, `_PALETTE`, `seed_plan()` y `SYSTEM_RULES` tal como estaban en `eb925b8` (subcategorías como `str`).
- `b5963a0e5c7c`: se copian `EXPENSE_ROOTS` (v2, con `is_fixed`), `LEGACY_SUBCATEGORY_MAP`, `SYSTEM_RULES` y `UNCATEGORIZED_EXPENSE` tal como están hoy, usando tuplas en vez de las dataclasses.
- Regla general: una migración es una foto del pasado y nunca importa de `app/` salvo para tipos estables. Se deja un comentario en ambas para que no se vuelva a hacer.
- Alternativa descartada: arreglar solo el `:name` con `sub.name`. Seguiría sembrando la taxonomía v2 en una migración que espera la original, y `b5963a0e5c7c` se rompería en el siguiente cambio del seed.

### D2 — `alembic upgrade head` en el arranque
- `docker-compose.yml`: `command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"`. Se monta también `alembic.ini` para que el contenedor use el del repo.
- `Dockerfile`: mismo orden en el `CMD`.
- Es idempotente: si la base ya está al día, Alembic no hace nada. Si una migración falla, el backend no arranca y el error queda en `docker compose logs backend`, en vez de servir 500.

### D3 — Test de instalación limpia
- `tests/test_migrations.py` crea una base temporal `<db>_migrations_<aleatorio>` en el mismo servidor, aplica `upgrade head` con la API de Alembic (`command.upgrade`) y comprueba: revisión actual = `head`, tablas principales presentes, 10 raíces de gasto de sistema con `Finanzas y Otros > Sin Clasificar`, y reglas de sistema. Al terminar borra la base.
- `env.py` acepta una URL inyectada por el test (`config.attributes["database_url"]`); si no hay, usa `DATABASE_URL` como hasta ahora.
- El usuario de Postgres del `docker-compose` puede crear bases; el test se salta con un mensaje claro si no tiene permiso.

## Risks / Trade-offs

- [Editar migraciones ya aplicadas] → solo cambia de dónde salen los datos, no qué datos ni qué esquema; las bases existentes no las vuelven a ejecutar.
- [El test tarda unos segundos más] → aceptable: es el único que vigila la instalación limpia.

## Migration Plan

Sin migraciones nuevas. Tras el cambio, comprobar con un volumen vacío (`docker compose -p expensetrack-clean …`) que la app arranca siguiendo el README.

## Open Questions

(ninguna)
