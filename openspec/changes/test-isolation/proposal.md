## Why

La revisión técnica del 2026-10-11 (`informe-ExpenseTrack.md`, hallazgo 🟡 «Los tests corren contra la BD de desarrollo y envían emails») comprobó que `pytest` usa el mismo `DATABASE_URL` que la app: tras una ejecución, Mailhog tenía 25 emails de prueba y las secuencias de la base de desarrollo habían avanzado (el siguiente usuario real se creó con id 182). Con un SMTP real en `.env`, los tests enviarían correo de verdad. Acordado con la autora el 2026-10-12.

## What Changes

- **Base de datos propia para los tests**: `pytest` usa `<POSTGRES_DB>_test` en el mismo servidor. Se crea de cero al empezar cada ejecución y se migra con `alembic upgrade head`, así que además cada ejecución vuelve a comprobar las migraciones.
- **Sin email en los tests**: el envío se desactiva siempre al correr `pytest`, sea cual sea el `.env`.
- **Un test que lo vigila**: falla si la base de los tests no termina en `_test` o si el SMTP está activo.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `local-setup`: los tests no tocan los datos de desarrollo ni envían correo.

## Impact

- **Backend**: `tests/conftest.py`, nuevo `tests/test_isolation.py`.
- **Docs**: README (sección Tests), `BUENAS_PRACTICAS.md` si menciona la BD de tests.
- **Datos**: la base de desarrollo deja de recibir usuarios y emails de prueba. Los que ya dejaron los tests anteriores no se borran (no se distinguen con seguridad de datos reales).
