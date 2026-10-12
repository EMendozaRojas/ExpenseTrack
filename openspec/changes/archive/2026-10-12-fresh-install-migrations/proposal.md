## Why

La revisión técnica del 2026-10-11 (`informe-ExpenseTrack.md`, hallazgos 🔴) encontró que la app **no arranca en una instalación limpia** siguiendo el README:

1. Nadie ejecuta las migraciones: ni el README ni el arranque del backend llaman a `alembic upgrade head`, así que el registro responde 500 (`relation "users" does not exist`).
2. Aunque se ejecuten, la cadena falla en `fac793ec36d3` con `cannot adapt type 'SeedSub'`: la migración importa el seed de categorías desde el código de la app (`app/db/seed_categories.py`), que cambió después (commit `a4203f2`). `b5963a0e5c7c` tiene el mismo problema latente.

Lleva un mes roto sin detectarse porque la base de datos de desarrollo se migró poco a poco y ningún test migra desde cero. Es el único hallazgo bloqueante de la revisión. Acordado con la autora el 2026-10-12.

## What Changes

- **Migraciones autocontenidas**: `fac793ec36d3` y `b5963a0e5c7c` dejan de importar `app.db.seed_categories` y llevan dentro una copia congelada de los datos que usaban cuando se escribieron (taxonomía original y taxonomía v2).
- **Migraciones al arrancar**: el backend ejecuta `alembic upgrade head` antes de levantar la API, tanto en `docker-compose.yml` como en el `CMD` del `Dockerfile`.
- **README**: explica que las migraciones se aplican solas y cómo ejecutarlas a mano.
- **Test de instalación limpia**: un test crea una base de datos vacía, aplica todas las migraciones y comprueba que el esquema y las categorías de sistema quedan bien.

## Capabilities

### New Capabilities

- `local-setup`: cómo se levanta el proyecto en local y qué garantías da (migraciones, tests, calidad).

### Modified Capabilities

(ninguna)

## Impact

- **Backend**: `alembic/versions/fac793ec36d3_*.py`, `alembic/versions/b5963a0e5c7c_*.py`, `alembic/env.py`, `Dockerfile`, nuevo `tests/test_migrations.py`.
- **Infra**: `docker-compose.yml` (comando del backend).
- **Docs**: `README.md`.
- **Datos**: ninguno. Las bases ya migradas no vuelven a ejecutar esas migraciones (Alembic guarda la revisión aplicada) y los datos que siembran son los mismos.
