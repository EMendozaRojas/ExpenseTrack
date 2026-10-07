## Purpose

Documentación OpenAPI de la API REST de ExpenseTrack, en español, servida en `/docs` y `/redoc` y versionada como `backend/openapi.json`: introducción, grupos, endpoints, errores y campos descritos, con tests que impiden que se degrade.

## ADDED Requirements

### Requirement: The API publishes a general introduction in Spanish
The OpenAPI document SHALL include, in Spanish, a title, a version and a Markdown description covering: what the API is for; how to authenticate (email/password login or Google, access token sent as `Authorization: Bearer`, refresh with the refresh token, logout, and how to use Swagger UI's "Authorize" button); the common conventions (decimal amounts serialized as strings, expenses as negative amounts, dates in ISO format and months as `YYYY-MM`, every resource isolated per user); and the error format. Swagger UI SHALL keep the authorization across page reloads.

#### Scenario: Introduction visible in the docs
- **WHEN** a developer opens `/docs`
- **THEN** the page shows the introduction with the authentication steps, the conventions and the error format, in Spanish

### Requirement: Endpoints are grouped by documented tags
Every operation SHALL belong to exactly one tag from a fixed list declared once: Autenticación, Usuario y perfil, Preferencias, Cuentas, Movimientos, Categorías, Reglas de categorización, Importación de extractos, Adjuntos, Tipos de cambio, Presupuestos, Metas de ahorro, Notificaciones, Dashboard, Análisis and Sistema. Each tag SHALL have a Spanish description. `GET /api/v1/expenses/summary` SHALL be grouped under Movimientos without changing its path, and `GET /health` under Sistema.

#### Scenario: Legacy expenses summary under Movimientos
- **WHEN** a developer looks for the monthly expense summary in `/docs`
- **THEN** `GET /api/v1/expenses/summary` appears in the Movimientos group, at the same path as before

#### Scenario: No undocumented groups
- **WHEN** the OpenAPI document is generated
- **THEN** every tag used by an operation is in the declared list and has a description

### Requirement: Every endpoint has a Spanish summary and description
Every operation SHALL declare an explicit Spanish summary and a Spanish description explaining what it does and the business rules that affect its result (for example: budget scope and read-only past months, the 30-day trash, import strategies, per-user isolation). Path and query parameters SHALL have a description, and an example when the format is not obvious (such as `YYYY-MM`). Operations that do not return JSON (file downloads, redirects) SHALL document their actual response content type or status.

#### Scenario: Budget update explains the scope
- **WHEN** a developer reads `PUT /api/v1/budgets/{category_id}/{period}` in `/docs`
- **THEN** the description explains `this` versus `following`, that individually planned months are kept, that past months return 409, and `period` is described with an example like `2026-10`

#### Scenario: File download documented
- **WHEN** a developer reads `GET /api/v1/attachments/{attachment_id}`
- **THEN** the response is documented as the file content with its media type, not as JSON

### Requirement: Error responses are documented with a common schema
Every operation SHALL document the error status codes it can return, each with a Spanish description of when it happens and an example body. Errors raised by the API SHALL be described with a common `ErrorResponse` schema (`{"detail": "<mensaje en español>"}`), and request validation errors with FastAPI's validation error schema. Every operation that requires authentication SHALL document 401. Documenting errors SHALL NOT change the status codes or messages the API returns.

#### Scenario: Conflict documented on budget creation
- **WHEN** a developer reads `POST /api/v1/budgets/`
- **THEN** the responses list 401, 404 (category not visible or not an expense category), 409 (duplicate in that month or past month) and 422, each with an example

#### Scenario: Behavior unchanged
- **WHEN** the existing test suite runs after the documentation is added
- **THEN** every test passes without changes to expected status codes or bodies

### Requirement: Schema fields are described with examples
Every property of every schema defined by the API (request bodies, responses and form bodies) SHALL have a Spanish description. Request schemas SHALL include an example value for each field. Only schemas generated internally by FastAPI for validation errors SHALL be exempt.

#### Scenario: Budget creation body documented
- **WHEN** a developer expands the `BudgetCreate` schema
- **THEN** each field (`category_id`, `year`, `month`, `amount`, `repeat`) shows a description and an example, and `repeat` explains that it defaults to repeating every month

### Requirement: The OpenAPI contract is versioned in the repository
The repository SHALL contain `backend/openapi.json`, the OpenAPI document generated from the application in a deterministic format, and a script to regenerate it. A test SHALL fail when the committed file differs from the document the application generates, telling how to regenerate it.

#### Scenario: Contract out of date
- **WHEN** a developer changes an endpoint and does not regenerate `openapi.json`
- **THEN** the snapshot test fails with a message indicating the regeneration command

#### Scenario: Regeneration is stable
- **WHEN** the script is run twice without code changes
- **THEN** the generated file is identical both times

### Requirement: A test prevents documentation from degrading
A test SHALL fail when any operation lacks an explicit summary or a description, lacks a declared tag, requires authentication but does not document 401, or when any non-exempt schema property lacks a description. The failure message SHALL name each offending operation or field.

#### Scenario: New endpoint without documentation
- **WHEN** a developer adds an endpoint without summary or description
- **THEN** the completeness test fails naming that endpoint

#### Scenario: New field without description
- **WHEN** a developer adds a field to a schema without a description
- **THEN** the completeness test fails naming the schema and the field
