## Context

- `tests/conftest.py` importa `engine` de `app.core.database`, creado con `get_settings().database_url` (la base de desarrollo). Cada test va dentro de una transacción con savepoint que se deshace al final, así que las filas no quedan, pero las secuencias sí avanzan y los efectos externos (emails a Mailhog) sí ocurren.
- `docker-compose.yml` fija `SMTP_HOST: mailhog` en el backend, y los tests corren dentro de ese contenedor.
- `get_settings()` está cacheado (`lru_cache`) y lee las variables de entorno la primera vez que se llama.

## Goals / Non-Goals

**Goals:** ejecutar `pytest` no deja rastro en la base de desarrollo ni envía correo; no hace falta configurar nada nuevo.

**Non-Goals:** contenedor de Postgres separado para tests; paralelizar los tests.

## Decisions

### D1 — Variables de entorno fijadas al principio de `conftest.py`
- Antes de importar nada de `app`, `conftest.py` calcula la URL de test (misma URL con la base `<nombre>_test`) y fija `DATABASE_URL` y `SMTP_HOST=""` en `os.environ`. Como `get_settings()` aún no se ha llamado, toda la app (engine incluido) usa esos valores.
- Si `DATABASE_URL` ya apunta a una base terminada en `_test` (por ejemplo en CI), se respeta.
- Alternativa descartada: un `.env.test` aparte. Habría que mantenerlo sincronizado con `.env` y es fácil olvidar usarlo.

### D2 — Base recreada y migrada en cada ejecución
- Fixture de sesión `autouse`: conectada a la base `postgres`, hace `DROP DATABASE IF EXISTS … WITH (FORCE)` + `CREATE DATABASE` y luego `alembic upgrade head` sobre ella.
- Coste: unos 2 segundos por ejecución. A cambio, cada ejecución parte de un estado conocido y vuelve a probar la instalación limpia.
- El patrón de transacción + savepoint por test se mantiene igual.

### D3 — Test de guarda
- `tests/test_isolation.py` comprueba que `get_settings().database_url` termina en `_test` y que `smtp_host` está vacío. Si alguien rompe el aislamiento, falla con un mensaje explícito.

## Risks / Trade-offs

- [El usuario de Postgres necesita permiso para crear bases] → lo tiene en `docker-compose` (es el dueño del servidor); en otro entorno el error lo dice claramente.
- [Si alguien importa `app` antes que `conftest.py`] → pytest siempre carga `conftest.py` antes que los módulos de test; el test de guarda lo detectaría.

## Migration Plan

Sin migraciones. La primera ejecución crea `expensetrack_test`.

## Open Questions

(ninguna)
