<!-- Revisado 2026-10-07 antes de archivar: specs ajustadas al comportamiento actual (Sin Clasificar como destino, subcategoría obligatoria). Las pantallas pendientes pasan a los changes `categories-screen`, `categorization-rules-screen` y `bulk-recategorize`. -->

## 1. Modelo y migración

- [x] 1.1 Ampliar `app/models/category.py`: `parent_id` self-FK (nullable), `kind` enum (`income`/`expense`), `icon` (str), `color` (str), `is_system` (bool); validar en el servicio que `parent_id` apunta a una raíz del mismo `kind` (un solo nivel)
- [x] 1.2 Crear `app/models/categorization_rule.py`: `match_type` enum (`contains`/`starts_with`), `pattern`, `category_id`, `priority` (int), `is_enabled` (bool), `owner_id` nullable (NULL = regla de sistema)
- [x] 1.3 Migración Alembic: columnas nuevas en `categories`; tabla `categorization_rules`; unicidad NULL-safe vía índice funcional `COALESCE(owner_id,-1), COALESCE(parent_id,-1), kind, name` (equivalente al `UNIQUE` + índice parcial planeado, cubre los mismos casos con un solo índice)
- [x] 1.4 Data-migration: (a) defaults en categorías existentes `kind='expense'`, `parent_id=NULL`, `is_system=(owner_id IS NULL)`; (b) renombrar colisiones con sufijo `(2)`,`(3)`… por orden de `id`; (c) insertar seed del Apéndice A con color por raíz; (d) insertar reglas de sistema del Apéndice B; verificado con `alembic upgrade head` + `downgrade` + `upgrade` de nuevo contra la base real (60 categorías de gasto, 20 de ingreso, 27 reglas)
- [x] 1.5 `app/db/seed_categories.py`: módulo de datos con el Apéndice A y B como estructura versionada, reutilizado por la data-migration

## 2. Servicio de categorización

- [x] 2.1 `app/services/categorizer.py`: `normalize(text)` según D3 (mayúsculas, sin acentos, sin `\d{4,}`, sin prefijos listados); test "COMPRA EN MERCADONA 1234" → matchea "MERCADONA"
- [x] 2.2 `match_category(texto, rules)`: reglas de usuario habilitadas por `priority DESC, id ASC`, luego sistema; primera que matchea gana
- [x] 2.3 Enganchado en la creación de `transaction` sin categoría; test: movimiento con concepto conocido queda categorizado, sin concepto conocido queda `category_id NULL`
- [x] 2.4 Validación de `match_type`: rechaza cualquier valor distinto de `contains`/`starts_with` (test 422, en creación y en `PATCH`)

## 3. API

- [x] 3.1 `app/routers/categories.py`: listado en árbol por `kind` (raíces + subcategorías, ordenado por nombre); alta con `parent_id`; borrado que reasigna movimientos y subcategorías al `parent` (o `NULL` si era raíz) y devuelve recuento afectado; tests de aislamiento y de "no se puede borrar `is_system`" (404, no revela existencia)
- [x] 3.2 `app/routers/categorization_rules.py`: CRUD + `GET /categorization-rules/preview?pattern=&match_type=` (no muta, devuelve recuento) + `POST /categorization-rules/{id}/apply` (solo `category_id IS NULL`, devuelve recuento actualizado); tests
- [x] 3.3 `POST /transactions/bulk-categorize`: sobrescribe categoría en la selección, ignora ids ajenos, devuelve recuento; tests
- [x] 3.4 Al crear/editar movimiento con categoría explícita, `source` de la categorización no se registra (D5: no hace falta para el MVP)

## 4. Frontend

- [x] 4.0 (no listada originalmente) `Category` en `types.ts` con `parent_id`/`kind`/`icon`/`color`/`is_system`/`children`; `flattenCategories()` para aplanar el árbol en selects; `categoriesById` en `TransactionsPage` incluye subcategorías (`Raíz · Sub`)
- [x] 4.4 Tests de `features/transactions` actualizados para el nuevo shape de `Category` (43 tests, 94.3% cobertura)

## 5. Verificación

- [x] 5.1 Backend `ruff`/`mypy`/`pytest --cov`: 42 tests, 92.35% (≥70%); Frontend `eslint`/`tsc`/`vitest --coverage`: 43 tests, 94.32% (≥70%)
- [x] 5.2 Smoke: verificado por tests de integración (usuario nuevo ve el seed; "COMPRA EN MERCADONA 1234" cae en Supermercado por regla de sistema; regla propia con preview/apply que solo rellena huecos; bulk-categorize sobrescribe e ignora ids ajenos; borrado de categoría con movimientos reasigna y reporta el recuento)

## Diferido

- 4.1 **Pendiente**: `features/categories/` con árbol navegable, alta/edición con color e icono, aviso "esto afecta a N movimientos" al borrar — hoy la única superficie de categorías en el frontend es el `<select>` aplanado dentro de `TransactionForm`; no hay pantalla de gestión de categorías → `categories-screen`
- 4.2 **Pendiente**: pestaña "Reglas" (CRUD, previsualizar, aplicar) — el backend está completo y testeado, sin UI → `categorization-rules-screen`
- 4.3 **Pendiente**: filtro "sin categorizar" y selección múltiple → `bulk-categorize` en la lista de movimientos; "crear regla para «COMERCIO»" al categorizar a mano — el backend (`bulk-categorize`, reglas) está listo, sin UI → `bulk-recategorize`
