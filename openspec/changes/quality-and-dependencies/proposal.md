## Why

La revisión técnica del 2026-10-11 (`informe-ExpenseTrack.md`, hallazgos 🟡 y nota «Buenas prácticas: 2») encontró que las herramientas de calidad están declaradas pero no se aplican, y dependencias con vulnerabilidades conocidas:

- `pip-audit`: 33 avisos en `starlette 0.41.3` (vía `fastapi 0.115.6`), `python-multipart 0.0.20`, `python-jose 3.3.0` y su dependencia `ecdsa`. `npm audit`: 7 en dependencias de desarrollo (2 críticas).
- `ruff check`: 62 avisos; `ruff format --check`: 34 archivos; `prettier --check`: 16 archivos; `mypy app`: 6 errores. Los hooks de pre-commit nunca se instalaron.
- `frontend/public/logo.png` pesa 1,6 MB y se sirve como favicon; `Design System/logo sin fondo listo.png` (1,8 MB) se subió pese a `--maxkb=1000`.
- No hay CI (no existe `.github/`).

Acordado con la autora el 2026-10-12: limpiar y activar los hooks, cambiar `python-jose` por PyJWT y añadir GitHub Actions.

## What Changes

- **Dependencias sin vulnerabilidades conocidas**: `fastapi` 0.143 (con `starlette` 1.x), `python-multipart` 0.0.32, `python-jose` → `PyJWT[crypto]` 2.15 (desaparece `ecdsa`); en el frontend, `npm audit fix` y `vitest`/`@vitest/coverage-v8` 3 → 5. `pip-audit` pasa a las dependencias de desarrollo.
- **Código al día con las herramientas**: `ruff check`, `ruff format`, `mypy app` (estricto), Prettier y ESLint sin avisos en todo el repo.
- **Hooks de pre-commit activables en esta máquina**: los que necesitan Node o las dependencias del proyecto (mypy, ESLint, Prettier) se ejecutan dentro de los contenedores con `docker compose exec`; ruff y los checks genéricos siguen con sus entornos propios. Los originales de `Design System/` quedan fuera del límite de tamaño.
- **Favicon ligero**: `logo.png` a 384×256 (de 1,6 MB a 110 KB).
- **CI con GitHub Actions**: en cada push y pull request, backend (ruff, formato, mypy, `pip-audit`, pytest con Postgres y cobertura) y frontend (ESLint, Prettier, tests con cobertura y build).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `local-setup`: el código cumple las herramientas de calidad, se comprueba en cada push y las dependencias no tienen vulnerabilidades conocidas.

## Impact

- **Backend**: `requirements*.txt`, `app/auth/security.py`, `app/services/google_oauth.py` (PyJWT), constantes HTTP renombradas por Starlette 1.x, correcciones de tipos en `recurring_detector`, `transactions`, `fx_rates` y `dashboard`, formato de todo `backend/`, `openapi.json` regenerado.
- **Frontend**: `package.json`/`package-lock.json`, formato de 10 archivos, `public/logo.png`.
- **Repo**: `.pre-commit-config.yaml`, nuevo `.github/workflows/ci.yml`, README y `BUENAS_PRACTICAS.md`.
- **Imagen Docker del backend**: hay que reconstruirla (`docker compose up --build`).
