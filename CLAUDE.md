# ExpenseTrack

## ¿Qué hace este proyecto?

Aplicación web personal para gestionar finanzas: cuentas, transacciones,
categorías (con reglas de categorización automática), presupuestos, metas
de ahorro, multi-moneda, adjuntos de recibos, importación de extractos
bancarios en CSV, y un dashboard mensual con insights (gastos recurrentes,
"gasto hormiga"). Ha crecido más allá de un simple registro de gastos hacia
una herramienta de finanzas personales.

Objetivo del proyecto: además de ser una herramienta de uso personal, sirve
como proyecto de aprendizaje de desarrollo asistido por IA (Python + FastAPI
+ React), orientado a construir portafolio para búsqueda de empleo en Madrid.

**Estado:** en desarrollo activo. El backend tiene API, modelos, migraciones
y tests para todas las features listadas abajo; el frontend tiene estructura
de API client, componentes y features con tests, aunque va por detrás del
backend en cobertura. Las features se planifican y documentan como "changes"
en `openspec/changes/` antes de implementarse (ver esa carpeta para el
roadmap y el detalle de cada feature).

## Tecnologías

| Capa | Tecnología | Notas |
|---|---|---|
| Frontend | React + TypeScript (Vite) | SPA separada, consume la API por HTTP |
| Backend | Python + FastAPI | API REST, validación con Pydantic, docs OpenAPI automáticas |
| Base de datos | PostgreSQL | corre en contenedor Docker |
| ORM / migraciones | SQLAlchemy + Alembic | estándar de la industria para FastAPI |
| Gestor de dependencias (Python) | pip + requirements.txt | |
| Autenticación | JWT (`python-jose`) + hash de contraseñas (`passlib`/`bcrypt`) + login social con Google (OAuth) y refresh tokens | multiusuario desde el inicio |
| Orquestación local | Docker Compose | levanta frontend, backend y db juntos; solo local por ahora, sin despliegue previsto |
| Tests backend | pytest | 15 módulos de test (auth, cuentas, transacciones, presupuestos, metas, multi-moneda, adjuntos, importaciones, insights, dashboard, login social, reglas de categorización...) |
| Tests frontend | Vitest + React Testing Library | con reporte de cobertura (`vitest --coverage`) |
| Routing frontend | React Router | |
| Data fetching frontend | TanStack Query | |
| Planificación de features | OpenSpec (`openspec/changes/`) | cada feature se propone y documenta como "change" antes de implementarse |

## Estructura de carpetas (real)

```
ExpenseTrack/
├── CLAUDE.md
├── BUENAS_PRACTICAS.md
├── docker-compose.yml
├── .env.example
├── openspec/            # propuestas y specs de cada feature (fuente de verdad del roadmap)
│   └── changes/
├── backend/
│   ├── app/
│   │   ├── auth/        # login, JWT, hash de contraseñas
│   │   ├── core/        # config y conexión a la base de datos
│   │   ├── db/          # seed de categorías
│   │   ├── models/      # modelos SQLAlchemy (user, account, transaction, category,
│   │   │                #   budget, savings_goal, attachment, fx_rate, import_batch...)
│   │   ├── schemas/     # esquemas Pydantic
│   │   ├── routers/     # endpoints (auth, accounts, transactions, categories,
│   │   │                #   budgets, goals, attachments, imports, insights, dashboard...)
│   │   ├── services/    # lógica de negocio (categorizador, FX, OAuth de Google,
│   │   │                #   parser de extractos, detector de recurrentes, storage...)
│   │   └── main.py
│   ├── alembic/         # migraciones
│   ├── scripts/         # seed de datos de prueba
│   ├── tests/           # 15 módulos de test con pytest
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── api/          # cliente de la API
    │   ├── components/
    │   └── features/
    ├── package.json
    └── Dockerfile
```

## Buenas prácticas

Ver [`BUENAS_PRACTICAS.md`](./BUENAS_PRACTICAS.md) para el detalle de
convenciones de código, testing, Docker y Git alineadas al estándar de
mercado 2026 para este stack.

## Cómo se corre en local

Copiar `.env.example` a `.env` y ajustar valores (`.env` nunca se commitea).
Las variables de Google OAuth son opcionales: sin ellas, el login social
simplemente responde 503 y el resto de la app funciona igual.

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend (API + docs): http://localhost:8000/docs
- Postgres: localhost:5432 (solo accesible desde los contenedores/host, no expuesto públicamente)

Para cargar datos de prueba realistas: `backend/scripts/seed_demo_data.py`.

## Cómo se corren los tests

**Backend:**
```bash
docker compose exec backend pytest
```

**Frontend:**
```bash
docker compose exec frontend npm test
```

## Documentación de la API

La API se documenta en español en http://localhost:8000/docs (Swagger) y
http://localhost:8000/redoc. El contrato OpenAPI está versionado en
`backend/openapi.json`. Después de cambiar un endpoint o un esquema, hay que
regenerarlo (un test falla si no está al día):

```bash
docker compose exec backend python -m scripts.export_openapi
```

Cada endpoint nuevo necesita `summary`, docstring, tag (`app/core/openapi.py`)
y errores documentados, y cada campo de un esquema, `Field(description=...)`
(con `examples` en los de entrada). Lo comprueba `tests/test_openapi_docs.py`.

## Decisiones tomadas

- Web app con frontend y backend separados (no SPA sin backend, no server-rendered).
- Backend en FastAPI en vez de Django/Flask: menor curva de aprendizaje, no se
  necesita admin panel ni templates (el frontend es una SPA independiente), y
  encaja mejor con el objetivo de aprender desarrollo asistido por IA
  (esquemas tipados con Pydantic, docs OpenAPI automáticas).
- Persistencia en PostgreSQL corriendo en Docker (no SQLite ni archivo plano),
  pensando en parecerse a un entorno de trabajo real.
- Todo el stack (frontend + backend + db) se levanta con Docker Compose.
- ORM: SQLAlchemy + Alembic para migraciones, por ser el estándar más pedido
  en ofertas de empleo con FastAPI (sobre SQLModel o SQL crudo).
- Dependencias Python con pip + requirements.txt, por simplicidad (sobre
  Poetry o uv).
- Autenticación con login desde el inicio (JWT, multiusuario): cada usuario
  gestiona solo sus propios gastos.
- Categorías de gasto mixtas: se cargan categorías predefinidas por defecto
  (seed data) y el usuario puede crear/editar las suyas.
- Sin despliegue previsto por ahora — uso solo en local, pero todo
  completamente dockerizado (frontend, backend y base de datos) desde el
  principio, para que correrlo sea siempre `docker compose up`.
- El alcance creció de "registro de gastos" a "finanzas personales": cuentas,
  transacciones, multi-moneda, presupuestos, metas de ahorro, adjuntos e
  importación de extractos bancarios.
- Autenticación ampliada con login social (Google OAuth) y refresh tokens,
  además del login con email/contraseña original.
- Cada feature se planifica primero como "change" en `openspec/changes/`
  (propuesta + specs + tareas) antes de implementarse, para mantener
  trazabilidad de decisiones de diseño.
