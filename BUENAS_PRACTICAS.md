# Buenas prácticas de ExpenseTrack

Basadas en el estándar de mercado 2026 para el stack elegido (FastAPI +
React/TypeScript + PostgreSQL + Docker). Pensadas para un proyecto personal
de aprendizaje, pero replicando prácticas reales de la industria, ya que uno
de los objetivos del proyecto es servir de portafolio.

## Backend (Python / FastAPI)

**Estructura en capas**, separando responsabilidades (ya reflejado en
`CLAUDE.md`): `routers` (endpoints) → `services` (lógica de negocio) →
`models`/`repositories` (acceso a datos) → `schemas` (validación
Pydantic). Nada de lógica de negocio dentro de los routers, y nunca todo el
backend en un solo `main.py`.

**Calidad de código:** [Ruff](https://docs.astral.sh/ruff/) para lint +
formato (reemplaza black, isort, flake8 y pyupgrade en una sola
herramienta) + **mypy** para chequeo de tipos. Se configuran ambos en
`pyproject.toml`.

**Tipado:** funciones y modelos siempre tipados; nada de `Any` salvo
justificación explícita.

**Configuración:** `pydantic-settings` para leer variables de entorno con
validación "fail fast" (el backend no arranca si falta una variable
requerida), en vez de leer `os.environ` sueltos por el código.

**Errores:** respuesta de error consistente en toda la API, con el formato
estándar de FastAPI: `{"detail": "<mensaje en español>"}` (en los errores de
validación `422`, `detail` es una lista con `loc`, `msg` y `type`). Se usan
`HTTPException` en vez de dejar que exploten errores no controlados, y los
errores de cada endpoint se documentan en OpenAPI con el esquema común
`ErrorResponse` (`app/core/openapi.py`).

**Testing:** `pytest`, con fixtures para la base de datos de test
(transacciones con rollback sobre la base de desarrollo, ver
`tests/conftest.py`). Cuando la lógica depende de la fecha, el "hoy" se fija
con un fixture (`set_today`) en vez de depender del reloj. Priorizar
tests de la lógica de negocio y de los endpoints críticos (crear/clasificar
gastos) sobre perseguir 100% de cobertura.

**Migraciones:** todo cambio de esquema pasa por Alembic. Nunca se modifica
la base de datos a mano.

## Frontend (React + TypeScript)

**TypeScript en modo `strict`**, evitando `any`; usar union types
discriminados para estados (ej. loading/error/success).

**Calidad de código:** ESLint (flat config) + Prettier.

**Estructura por features**, no por tipo de archivo: cada funcionalidad
(ej. `transactions/`, `budgets/`, `auth/`) agrupa sus propios componentes,
hooks y tipos; `src/components/` queda solo para piezas compartidas (layout,
modal…).

**Estado:** `useState`/`useReducer` para estado local de UI, **TanStack
Query** para todo lo que venga del backend (fetch, cache, invalidación) en
vez de guardar datos de servidor en estado global. Nada de Redux para un
proyecto de este tamaño.

**Testing:** Vitest + React Testing Library, enfocado en comportamiento
(qué ve/hace el usuario) más que en detalles de implementación.

## Diseño de la API

- Prefijo de versión en la URL: `/api/v1/...`, para poder introducir cambios
  incompatibles en el futuro sin romper el frontend actual.
- Recursos en plural: `/transactions`, `/categories`, no verbos en la URL
  (salvo acciones explícitas como `/accounts/{id}/archive`).
- Códigos HTTP correctos (`201` al crear, `404` si no existe, `422` en
  validación fallida, etc.).
- Paginación por cursor en los listados que crecen sin límite (movimientos:
  `/transactions?limit=50&cursor=...`, con `next_cursor` en la respuesta),
  que no repite ni salta elementos aunque se inserten datos nuevos.
- Documentación en español en `/docs` y contrato versionado en
  `backend/openapi.json`; tests que fallan si un endpoint o un campo queda
  sin documentar o si el contrato no está al día.

## Docker

- **Multi-stage builds** en ambos Dockerfiles: hoy hay una etapa `base` y
  una `dev` (con dependencias de desarrollo y recarga en caliente). Como no
  hay despliegue previsto, la etapa final mínima de producción se añadirá
  cuando haga falta.
- Contenedores corren con **usuario no-root**.
- `.dockerignore` en ambos proyectos (mínimo: `.env`, `.git`,
  `__pycache__`, `node_modules`).
- El `.env` **nunca** se copia dentro de la imagen (`COPY .env` queda
  prohibido) — las variables se inyectan en tiempo de ejecución vía
  Docker Compose.

## Configuración y secretos

- `.env.example` versionado en el repo con las variables necesarias (sin
  valores reales); `.env` real en `.gitignore`, nunca commiteado.
- Ninguna credencial (contraseña de Postgres, secret de JWT, etc.) vive en
  el código ni en el Dockerfile.

## Git y commits

- **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `test:`,
  `refactor:`) para mensajes de commit consistentes y legibles en el
  historial.
- **Pre-commit hooks** (via [pre-commit](https://pre-commit.com/)) que
  corren Ruff, mypy, ESLint y Prettier automáticamente antes de cada
  commit, para no depender de acordarse de correrlos a mano.
- Commits pequeños y con un solo propósito, aunque sea un proyecto de una
  sola persona — así se ve y se practica como se trabaja en equipo.

## CI y cobertura

- **CI (GitHub Actions):** se deja para más adelante — el proyecto es solo
  local por ahora y aún no hay repo remoto. Mientras tanto, la calidad se
  garantiza con **pre-commit hooks** (ver [`.pre-commit-config.yaml`](./.pre-commit-config.yaml)),
  que corren Ruff, mypy y los checks básicos antes de cada commit.
- **Cobertura mínima de tests: 70%**, medida con `coverage.py` en el
  backend y con el reporte de cobertura de Vitest en el frontend. Es un
  piso, no un objetivo a perseguir con tests superficiales.

## Pre-commit hooks

Instalación (una sola vez por entorno):

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

A partir de ahí, cada `git commit` corre automáticamente Ruff (lint +
formato), mypy, y validación de que el mensaje siga Conventional Commits.
Configuración completa en [`.pre-commit-config.yaml`](./.pre-commit-config.yaml).
