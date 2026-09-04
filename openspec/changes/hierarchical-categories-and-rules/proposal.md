## Why

Las categorías actuales son planas y sin tipo (no distinguen ingreso de gasto). Un PFM necesita jerarquía (subcategorías), distinción ingreso/gasto, y un motor de reglas por palabra clave que clasifique automáticamente los movimientos importados y los manuales, además de recategorización en lote para limpiar datos rápido.

## What Changes

- `categories` gana `parent_id` (jerarquía de 1 nivel), `kind` (`income` | `expense`), `icon`, `color`, `is_system`.
- Constraint de unicidad `(owner_id, parent_id, name, kind)` y unicidad de las categorías del sistema (`owner_id IS NULL`).
- Seed de categorías del sistema con subcategorías (12 raíces de gasto, 6 de ingreso — lista completa en `design.md` Apéndice A), vía data-migration. "Sin categoría" = `category_id NULL`, no una categoría real.
- Nuevo recurso `categorization-rules`: `match_type` (`contains` | `starts_with` — sin `regex` en el MVP), `pattern`, `category_id`, `priority`, `is_enabled`; reglas del usuario tienen prioridad sobre las del sistema. Reglas de sistema iniciales en `design.md` Apéndice B.
- Aplicación de reglas: al crear/importar un movimiento sin categoría, el sistema intenta asignar una según las reglas (sobre la descripción normalizada). `GET /categorization-rules/preview` devuelve cuántos movimientos existentes haría match; `POST /categorization-rules/{id}/apply` solo rellena movimientos sin categoría (nunca sobrescribe).
- `POST /transactions/bulk-categorize` para asignar categoría a varios movimientos a la vez; esta acción manual **sí** sobrescribe la categoría previa.
- Al categorizar manualmente un movimiento, el frontend ofrece "crear regla para este comercio".
- Borrar una categoría propia con hijos o movimientos: reasigna a su `parent` (o a `NULL` si era raíz), nunca deja movimientos colgando. Las categorías del sistema no se borran; ocultarlas queda fuera del MVP.

## Capabilities

### New Capabilities
- `categories`: taxonomía de ingresos y gastos del usuario, con jerarquía de un nivel, categorías del sistema compartidas y categorías propias, y reglas de borrado que nunca dejan movimientos sin categoría válida.
- `categorization-rules`: reglas por patrón de texto que asignan automáticamente una categoría a los movimientos, con prioridad y previsualización de impacto.

### Modified Capabilities

(ninguna archivada — `transactions` de `accounts-and-transactions` aún no estará archivada; la interacción "aplicar reglas al crear/importar" se especifica aquí como parte de `categorization-rules`.)

## Impact

- **Backend**: `app/models/category.py` (nuevos campos + self-FK), `app/models/categorization_rule.py`, `app/routers/categories.py` (árbol, borrado con reasignación), `app/routers/categorization_rules.py`, servicio `categorizer.py` (normalización + match), migración Alembic con seed, `bulk-categorize` en `transactions`.
- **Frontend**: `features/categories/` (árbol, color/icono), pestaña "Reglas", filtro "sin categorizar" y selección múltiple en la lista de movimientos.
- **Dependencias**: sin nuevas (regex con `re` de stdlib).
- **Orden**: depende de `accounts-and-transactions`.
