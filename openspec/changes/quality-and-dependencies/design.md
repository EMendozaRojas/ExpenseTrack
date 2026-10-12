## Context

- En la máquina de desarrollo no hay `node`, `npm`, `pip` ni `pre-commit` fuera de Docker: todo corre en los contenedores. Los hooks locales de ESLint y Prettier (`npm --prefix frontend …`) y el de mypy (entorno aislado sin las dependencias del proyecto) no podían funcionar tal como estaban.
- `starlette` corrige sus avisos a partir de 1.3.1, y solo FastAPI ≥ 0.12x la admite; `python-jose` está sin mantener y su dependencia `ecdsa` tiene un aviso sin corrección.

## Goals / Non-Goals

**Goals:** `pip-audit` y `npm audit` a cero; todas las herramientas de calidad en verde; los hooks funcionan en esta máquina; GitHub comprueba cada push.

**Non-Goals:** reescribir el historial de git (los commits anteriores a octubre siguen sin Conventional Commits); actualizar dependencias sin avisos (SQLAlchemy, Pydantic…) solo por estar al día; sustituir `passlib` (avisa de `crypt` en Python 3.13, queda anotado).

## Decisions

### D1 — Saltos de versión acotados a lo que tiene avisos
- `fastapi` 0.115.6 → 0.143.0 (arrastra `starlette` 1.7.0). Cambios necesarios: `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT` y `HTTP_413_REQUEST_ENTITY_TOO_LARGE` → `HTTP_413_CONTENT_TOO_LARGE`; los campos de archivo se describen en OpenAPI con `contentMediaType` (el test de documentación lo acepta) y se regenera `openapi.json`.
- `python-jose` → `PyJWT[crypto]`: misma API (`jwt.encode`/`jwt.decode`), la excepción pasa a `jwt.PyJWTError`. Mismo algoritmo y secreto: las sesiones abiertas siguen siendo válidas.
- `vitest` 3 → 5: los 144 tests pasan sin cambios. **Ojo con la cobertura**: con el mismo código, Vitest 3 mide 93,95 % de líneas y Vitest 5, 86,36 %, porque el remapeo de la cobertura es más estricto (cuenta los archivos solo de tipos y las funciones de `api.ts` que los tests simulan). No es una bajada real; el umbral del 70 % se mantiene.

### D2 — Hooks que funcionan sin Node ni pip en el host
- ruff (`ruff-pre-commit`), los checks genéricos y `conventional-pre-commit` siguen como están: `pre-commit` les crea su propio entorno.
- mypy, ESLint y Prettier pasan a hooks `local` con `language: system` y `entry: docker compose exec -T <servicio> …`: usan exactamente las versiones y dependencias del proyecto. Requieren el stack levantado al hacer commit; si no lo está, el hook falla con un mensaje claro y basta con `docker compose up -d`.
- `check-added-large-files` excluye `^Design System/` (originales de diseño, intencionadamente a tamaño completo).
- La instalación de `pre-commit` necesita `sudo` (no hay `pip` en el host): `sudo apt install pre-commit` y `pre-commit install --hook-type pre-commit --hook-type commit-msg`. La hace la autora; el CI cubre lo mismo aunque el hook no esté.

### D3 — CI en GitHub Actions
- `.github/workflows/ci.yml`, en `push` y `pull_request`:
  - **backend**: Python 3.12, servicio `postgres:16-alpine`, `pip install -r requirements-dev.txt`, `ruff check`, `ruff format --check`, `mypy app`, `pip-audit -r requirements.txt` y `pytest --cov` (el umbral del 70 % está en `pyproject.toml`). Los tests crean su base `_test` y aplican las migraciones desde cero, así que el CI también vigila la instalación limpia.
  - **frontend**: Node 22, `npm ci`, `npm run lint`, `npm run format:check`, `npm run test:coverage` y `npm run build` (que incluye `tsc -b`).
- `pip-audit` en el CI puede fallar el día que se publique un aviso nuevo: es intencionado, porque es el momento de actualizar.

## Risks / Trade-offs

- [Salto grande de FastAPI] → cubierto por los 194 tests del backend (HTTP contra Postgres real) y el snapshot de OpenAPI.
- [Diff de formato grande] → el formato no cambia la lógica; los cambios que sí la tocan (PyJWT, constantes HTTP, tipos) se enumeran en el mensaje del commit.

## Migration Plan

Reconstruir la imagen del backend (`docker compose up -d --build backend`). Sin migraciones de base de datos.

## Open Questions

(ninguna)
