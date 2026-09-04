## Context

Ver `proposal.md` — Why. Depende de `accounts-and-transactions` (recurso `transactions`, importe firmado). Estado actual: `Category(id, name, owner_id nullable, created_at)`, sin jerarquía ni tipo, sin seed. Este documento recoge las **decisiones abiertas** para la revisión.

## Goals / Non-Goals

**Goals:**
- Jerarquía de categorías de un nivel, con tipo ingreso/gasto.
- Categorías del sistema por defecto + categorías propias.
- Motor de reglas por texto con prioridad y previsualización.
- Recategorización en lote.

**Non-Goals:**
- Clasificación por ML / aprendizaje del histórico del usuario (posible fase posterior; las reglas son la base).
- Reglas por importe, cuenta o fecha (solo por texto del concepto en este cambio).
- Jerarquía de más de un nivel.

## Decisions

> Estado de la revisión (2026-09-01): D1–D8 resueltas.

### D1 — Profundidad de la jerarquía — DECIDIDO: un solo nivel
- `parent_id` apunta siempre a una categoría raíz (`parent_id IS NULL`); una subcategoría no puede tener hijas. Se valida en el servicio al crear/editar.
- Alternativa descartada: árbol arbitrario (`ltree` / CTE recursivo) — complejidad de UI y de queries innecesaria.

### D2 — Seed de categorías del sistema — DECIDIDO: lista aprobada tal cual
- Se implementa el conjunto del **Apéndice A** de este documento (12 raíces de gasto, 6 de ingreso, con subcategorías) más las reglas de sistema iniciales del **Apéndice B**.
- Todas con `owner_id NULL`, `is_system=true`. Iconos: emoji (ver Open Questions, no bloquea). Colores: paleta asignada por raíz en la data-migration.

### D3 — Normalización de la descripción antes del match — DECIDIDO
- `normalize(text)` =: pasar a mayúsculas → quitar acentos/diacríticos → colapsar espacios → eliminar secuencias `\d{4,}` (números de tarjeta/cuenta) → eliminar los prefijos `COMPRA EN`, `PAGO EN`, `PAGO`, `RECIBO`, `ADEUDO`, `BIZUM DE`, `BIZUM A`, `TRANSFERENCIA DE`, `TRANSFERENCIA A`, `TRANSFERENCIA` → recortar.
- La lista de prefijos es ampliable en el futuro sin cambiar el spec (es detalle de implementación del servicio).

### D4 — `match_type` — DECIDIDO: solo `contains` y `starts_with` (sin `regex` en el MVP)
- El enum de `match_type` es `contains | starts_with`. Sin `regex`: evita ReDoS y regex inválidas en la UI, y cubre la práctica totalidad del matching de conceptos bancarios.
- Orden de resolución: reglas del usuario habilitadas por `priority DESC`, luego `id ASC`; después reglas del sistema. La primera que hace match gana.
- `regex` se podrá añadir más adelante como cambio aparte si surge la necesidad.

### D5 — Aplicación de reglas — DECIDIDO: "rellenar huecos"
- Las reglas **no** se aplican automáticamente al crearlas/editarlas. Acción explícita `POST /categorization-rules/{id}/apply`.
- `apply` (y la aplicación automática al crear/importar un movimiento) solo tocan movimientos **sin categoría** (`category_id IS NULL`). Nunca pisan una categoría existente, venga de otra regla o puesta a mano.
- `POST /transactions/bulk-categorize` **sí** puede sobrescribir categorías existentes: es una acción manual y explícita del usuario sobre una selección concreta.
- No hace falta registrar el origen (regla vs manual) de cada categorización para el MVP.

### D6 — "Sin categoría" — DECIDIDO: `category_id NULL`
- No hay categoría real "Sin categoría"; un movimiento sin clasificar tiene `category_id NULL`. Encaja con el filtro `uncategorized=true` de `transactions`.

### D7 — Borrado de categoría / ocultar del sistema — DECIDIDO
- Al borrar una categoría propia: sus movimientos y subcategorías se reasignan al `parent` de la categoría borrada; si era raíz, a `NULL`. El endpoint devuelve el recuento de movimientos afectados; el frontend lo muestra antes de confirmar.
- Las categorías del sistema (`is_system=true`) **no se pueden borrar**.
- **Ocultar categorías del sistema queda fuera de alcance del MVP.** El usuario que no use una categoría simplemente no la selecciona. Se revisará si el seed resulta ruidoso en uso real (sería una tabla `hidden_system_categories` por usuario, aditiva).

### D8 — Migración de las categorías actuales — DECIDIDO: renombrar con sufijo en colisión
- Todas las existentes pasan a `kind='expense'`, `parent_id NULL`, `is_system = (owner_id IS NULL)`.
- Si dos categorías del mismo usuario colisionan con la unicidad nueva `(owner_id, parent_id, name, kind)`, la segunda y siguientes se renombran `Nombre (2)`, `Nombre (3)`… No se fusionan movimientos (no destructivo; el usuario fusiona a mano si quiere).
- Colisión de una categoría de usuario con una del sistema del mismo nombre: se respeta la de usuario (distinto `owner_id`, la unicidad no aplica entre ámbitos).

## Risks / Trade-offs

- [Seed grande y opinado que luego no gusta] → mantenerlo en un único módulo de datos versionado (`app/db/seed_categories.py`); cambios posteriores por nueva migración. Si genera ruido, se añade el ocultar-por-usuario (D7).
- [Recategorización en lote irreversible] → `apply` solo rellena huecos (no borra nada); `bulk-categorize` sí sobrescribe pero es selección explícita — el frontend muestra el recuento antes de ejecutar.
- [Unicidad nueva rompe la migración] → estrategia de sufijo en D8; la data-migration debe detectar colisiones dentro de cada `(owner_id, parent_id, kind)` y renombrar de forma determinista (orden por `id`).
- [`starts_with`/`contains` sobre descripción sin normalizar falla] → el match SIEMPRE opera sobre `normalize(raw_description)` (D3), nunca sobre el texto crudo; test explícito con "COMPRA EN MERCADONA 1234".

## Migration Plan

1. Migración de esquema: añadir `parent_id` (self-FK), `kind` (enum), `icon`, `color`, `is_system` a `categories`; crear `categorization_rules` (`owner_id` nullable, `match_type` enum `contains|starts_with`, `pattern`, `category_id`, `priority`, `is_enabled`); constraint `UNIQUE (owner_id, parent_id, name, kind)` + índice parcial único para el sistema (`WHERE owner_id IS NULL`).
2. Data-migration:
   a. `UPDATE categories SET kind='expense', parent_id=NULL, is_system=(owner_id IS NULL)`.
   b. Resolver colisiones de unicidad renombrando con sufijo `(2)`, `(3)`… por orden de `id` (D8).
   c. Insertar el seed del **Apéndice A** (`is_system=true`, `owner_id NULL`, color por raíz).
   d. Insertar las reglas de sistema del **Apéndice B**.
3. Rollback: `downgrade` borra las filas `is_system=true AND owner_id IS NULL`, la tabla `categorization_rules` y las columnas nuevas. El renombrado con sufijo de 2.b no se revierte (inocuo).

## Open Questions

- Iconos: se usarán emoji en el seed (campo `icon` como string). Cambiar a un set SVG es solo frontend, no toca spec.
- `sort_order` manual de categorías para el frontend: ampliable después sin romper nada; no bloquea.

## Apéndice A — Seed de categorías del sistema

**Gasto** (raíz → subcategorías):

- **Vivienda**: Alquiler / Hipoteca · Comunidad · Suministros (luz, agua, gas) · Internet y teléfono · Mantenimiento y reparaciones · Seguro de hogar
- **Alimentación**: Supermercado · Mercado y panadería
- **Restauración**: Restaurantes · Bares y cafeterías · Comida a domicilio
- **Transporte**: Transporte público · Combustible · Parking y peajes · Taxi / VTC · Mantenimiento del vehículo · Seguro del coche · Impuestos e ITV
- **Salud**: Farmacia · Médico y dentista · Seguro médico · Óptica · Gimnasio y deporte
- **Ocio**: Cine, teatro y eventos · Libros, música y juegos · Suscripciones · Viajes y vacaciones · Aficiones
- **Compras**: Ropa y calzado · Electrónica · Hogar y decoración · Cuidado personal · Regalos
- **Educación**: Matrículas y cursos · Material y libros · Idiomas
- **Finanzas**: Comisiones bancarias · Intereses de préstamos · Impuestos y tasas · Asesoría
- **Mascotas**: Comida y accesorios · Veterinario
- **Familia e hijos**: Guardería y colegio · Ropa y juguetes · Actividades
- **Otros gastos**: Retiradas de efectivo · Donativos · Sin clasificar

**Ingreso** (raíz → subcategorías):

- **Nómina y salario**: Nómina · Pagas extra · Bonus
- **Trabajo autónomo**: Facturas a clientes
- **Rendimientos**: Intereses · Dividendos · Alquileres cobrados
- **Reembolsos**: Devoluciones de compras · Devolución de Hacienda · Gastos compartidos
- **Ayudas y prestaciones**: Subvenciones · Prestaciones
- **Otros ingresos**: Regalos recibidos · Sin clasificar

## Apéndice B — Reglas de sistema iniciales

Todas `match_type=contains`, `owner_id NULL`, `priority=0`, sobre descripción normalizada:

| Patrón | Categoría destino |
|---|---|
| `MERCADONA`, `CARREFOUR`, `LIDL`, `DIA`, `ALCAMPO`, `EROSKI`, `CONSUM` | Supermercado |
| `REPSOL`, `CEPSA`, `GALP`, `BP`, `SHELL` | Combustible |
| `NETFLIX`, `SPOTIFY`, `HBO`, `DISNEY`, `AMAZON PRIME`, `FILMIN` | Suscripciones |
| `EMT`, `METRO`, `RENFE`, `CERCANIAS`, `EMT MADRID` | Transporte público |
| `FARMACIA` | Farmacia |
| `GLOVO`, `UBER EATS`, `JUST EAT`, `DELIVEROO` | Comida a domicilio |
| `AMAZON`, `AMZN` | Sin clasificar (solo si no matchea Prime) |

> Nota: el patrón `BIZUM` **no** lleva regla de categoría; solo se limpia como prefijo en `normalize()` (D3).
