# ExpenseTrack

## ¿Qué hace este proyecto?

Aplicación web personal para gestionar gastos mensuales. Permite registrar
gastos, asignarles una categoría, y ver un resumen/clasificación de gastos
agrupados por mes (cuánto se gastó, en qué categorías, evolución mes a mes).

Objetivo del proyecto: además de ser una herramienta de uso personal, sirve
como proyecto de aprendizaje de desarrollo asistido por IA (Python + FastAPI
+ React), orientado a construir portafolio para búsqueda de empleo en Madrid.

**Estado:** en fase de diseño inicial. Aún no hay código — este documento es
el primer artefacto del proyecto y se irá corrigiendo a medida que se tomen
más decisiones.

## Tecnologías

| Capa | Tecnología | Notas |
|---|---|---|
| Frontend | React + TypeScript (Vite) | SPA separada, consume la API por HTTP |
| Backend | Python + FastAPI | API REST, validación con Pydantic, docs OpenAPI automáticas |
| Base de datos | PostgreSQL | corre en contenedor Docker |
| ORM / migraciones | SQLAlchemy + Alembic | estándar de la industria para FastAPI |
| Gestor de dependencias (Python) | pip + requirements.txt | |
| Autenticación | JWT (ej. `python-jose`) + hash de contraseñas (`passlib`) | multiusuario desde el inicio |
| Orquestación local | Docker Compose | levanta frontend, backend y db juntos; solo local por ahora, sin despliegue previsto |
| Tests backend | pytest | |
| Tests frontend | Vitest + React Testing Library | |

## Estructura de carpetas (propuesta)

```
ExpenseTrack/
├── CLAUDE.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── auth/       # login, JWT, hash de contraseñas
│   │   ├── models/     # modelos SQLAlchemy (User, Expense, Category)
│   │   ├── schemas/    # esquemas Pydantic
│   │   ├── routers/    # endpoints (auth, expenses, categories)
│   │   └── main.py
│   ├── alembic/        # migraciones
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    ├── tests/
    ├── package.json
    └── Dockerfile
```

## Buenas prácticas

Ver [`BUENAS_PRACTICAS.md`](./BUENAS_PRACTICAS.md) para el detalle de
convenciones de código, testing, Docker y Git alineadas al estándar de
mercado 2026 para este stack.

## Cómo se corre en local

> Pendiente de confirmar puertos y variables de entorno exactas cuando se
> cree el `docker-compose.yml`.

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend (API + docs): http://localhost:8000/docs
- Postgres: localhost:5432 (solo accesible desde los contenedores/host, no expuesto públicamente)

## Cómo se corren los tests

**Backend:**
```bash
docker compose exec backend pytest
```

**Frontend:**
```bash
docker compose exec frontend npm test
```

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
