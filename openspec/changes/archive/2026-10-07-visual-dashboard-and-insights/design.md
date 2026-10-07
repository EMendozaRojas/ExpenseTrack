> **Revisión 2026-10-07 (antes de archivar):** este design describe el plan original (endpoints `/stats/*` por rangos, Recharts, tasa de ahorro). Lo implementado es un resumen mensual único (`GET /dashboard/summary`) con gráficas propias, recurrentes que se descartan por serie y gasto hormiga por subcategoría. Ver las specs y la sección "Diferido" de tasks.md.

## Context

Ver `proposal.md` — Why. Depende de `accounts-and-transactions` y `hierarchical-categories-and-rules`. Restricción del frontend: los artefactos y dependencias deben funcionar en local sin CDN externo (alineado con `BUENAS_PRACTICAS.md` y el patrón de artifacts). Este documento recoge las **decisiones abiertas** para la revisión.

## Goals / Non-Goals

**Goals:**
- Endpoints de agregación rápidos y parametrizables por rango y granularidad.
- Tres gráficas de la visión (dona, barras, línea) + tiles.
- Diagnóstico: top categorías, recurrentes, gasto hormiga.

**Non-Goals:**
- Predicción de gasto futuro / forecasting.
- Exportación de informes en PDF.
- Alertas derivadas de insights (podrían venir después; aquí solo se detecta y se muestra).

## Decisions

> Estado de la revisión (2026-09-04): D1–D9 resueltas.

### D1 — Librería de gráficas — DECIDIDO: Recharts
- API declarativa React con dona/barras/línea/tooltips/leyenda/responsive de serie; se bundlea con Vite (sin CDN); compatible con React 19 (v2.13+). La guía `dataviz` sigue aplicando para paleta y espaciado (tokens de tema claro/oscuro).
- Alternativas descartadas: Visx (más control, más código para 3 gráficas estándar), SVG a mano (cero deps pero reimplementar ejes/tooltips/leyenda no compensa aquí).

### D2 — Granularidades — DECIDIDO
- `day`, `week`, `month`, `year` + rango `custom`. Semana **ISO, empieza lunes** (`date_trunc('week', ...)` de Postgres ya es lunes-based). Buckets calculados en SQL.

### D3 — Zona horaria — DECIDIDO
- Los rangos relativos ("hoy", "esta semana") se resuelven con un default configurable **`Europe/Madrid`**; si `user_preferences.timezone` existe (cambio `multicurrency-social-auth-attachments`), se usa esa — dependencia blanda, sin orden forzado entre cambios. `posted_at` es `date` sin hora, así que el efecto se limita al borde del rango.

### D4 — Multi-moneda — DECIDIDO
- Agregación **por moneda** en el MVP; cada serie/porción lleva su `currency`. `convert_to` opcional lo añade `multicurrency-social-auth-attachments`.

### D5 — Rendimiento — DECIDIDO: queries directas, sin vista materializada
- Índices `(owner_id, posted_at)` y `(owner_id, category_id, posted_at)`. A escala de un usuario (miles de filas) agrega en milisegundos. `mv_monthly_category_totals` queda como plan B solo si se mide lentitud real — no se construye en este cambio.

### D6 — Detección de recurrentes — DECIDIDO
- Normalizar `counterparty` (mismo `normalize()` de `hierarchical-categories-and-rules`); agrupar por contraparte normalizada, en ambas direcciones (gasto e ingreso, p. ej. nómina).
- Serie si hay **≥3 ocurrencias** con separación temporal consistente: gap mediano mensual (26–35 días) / semanal (6–8 días) / anual (350–380 días), y todos los importes dentro de **±25%** de la mediana (banda más laxa para cazar suscripciones que suben de precio o recibos variables como luz/agua, a costa de más falsos positivos que el usuario descarta).
- Cálculo **bajo demanda**: `GET /insights/recurring` recalcula en vivo sobre los últimos 6 meses. La tabla `recurring_series` solo persiste la decisión `confirmed`/`dismissed` del usuario por contraparte normalizada — no un job de fondo.

### D7 — "Gasto hormiga" configurable — DECIDIDO
- Los umbrales son **configurables por el usuario**, no constantes fijas. Nueva tabla `insight_settings` (`owner_id` PK/FK, `ant_expense_max_amount` `Numeric(10,2)` default **10.00**, `ant_expense_min_count` int default 5, `ant_expense_min_aggregate` `Numeric(10,2)` default 30.00, `updated_at`), creada perezosamente con defaults si el usuario nunca la tocó.
- Definición: en el rango consultado, agrupar gastos con `amount ≤ ant_expense_max_amount` por contraparte normalizada; reportar el grupo si `count(grupo) ≥ ant_expense_min_count` **y** `sum(grupo) ≥ ant_expense_min_aggregate`. No se persiste como serie.
- `GET /insights/settings` (lee, con defaults si no existe fila) y `PATCH /insights/settings` (crea/actualiza) — panel dedicado en `/insights`. `GET /insights/ant-expense` siempre usa los valores guardados del usuario.

### D8 — Retirar `GET /expenses/summary` — DECIDIDO
- Se retira. El frontend migra a `/stats/summary` + `/stats/by-category` en este mismo cambio.
- Nota de spec: la ruta nunca se formalizó como un `Requirement` en `specs/transactions/spec.md` de `accounts-and-transactions` (se mencionó solo en su `proposal.md`/`tasks.md` como detalle de implementación). Retirarla es, por tanto, una tarea de implementación, no una entrada `REMOVED` en ninguna spec.

### D9 — Marcos financieros de referencia — DECIDIDO
- `GET /stats/summary` añade `savings_rate = (ingresos − gastos) / ingresos` del rango y su `tier` (crítico/bajo/medio/bueno/muy bueno/FIRE), calculado en backend. Tile en el dashboard.
- La insight "categorías de mayor impacto" añade, **solo para categorías raíz**, `share_pct` (share sobre el gasto total del rango) y `over_typical` (`true` si supera la banda de referencia del Apéndice A: Vivienda >35, Transporte >20, Alimentación >15). El frontend resalta las `over_typical`.
- Alcance: señales de solo lectura; sin alertas ni acciones automáticas (coherente con Non-Goals).

## Risks / Trade-offs

- [Agregar en Python como hace hoy `summary`] → todos los endpoints nuevos agregan en SQL (`SUM`, `date_trunc`, `GROUP BY`); prohibido sumar en el handler.
- [Dashboard lento con muchos datos] → índices primero, vista materializada como plan B medido (D5), no construida en este cambio.
- [Recurrentes con falsos positivos, más con banda ±25%] → se presentan como sugerencias no confirmadas; el usuario acepta/descarta; nunca se actúa solo sobre ellas. El recálculo bajo demanda (no persistido salvo la decisión) evita arrastrar falsos positivos indefinidamente.
- [Umbrales de gasto hormiga mal calibrados por defecto] → configurables por usuario desde el primer día (D7); 10€/5 movs/30€ son solo el default inicial.
- [`insight_settings` inexistente para un usuario nuevo] → `GET /insights/settings` devuelve los defaults sin crear fila; `PATCH` crea/actualiza (upsert). `GET /insights/ant-expense` nunca falla por falta de configuración.
- [Retirar `/expenses/summary` rompe algo que dependía de él] → solo lo consume `MonthlyExpensesPage`, que se reescribe en este mismo cambio; sin otros consumidores conocidos.

## Migration Plan

1. Migración de esquema: `recurring_series` (owner_id, counterparty_normalized, status `confirmed`/`dismissed`, decided_at) + `insight_settings` (owner_id PK, ant_expense_max_amount, ant_expense_min_count, ant_expense_min_aggregate, updated_at).
2. Sin data-migration (los insights se calculan sobre los datos existentes; `insight_settings` se crea perezosamente).
3. Eliminar la ruta `GET /expenses/summary` y su router/tests (tarea de implementación, no de esquema).
4. Rollback: `downgrade` elimina las tablas nuevas.

### D10 — Selector de rango sincronizado con la URL — CONFIRMADO
- El rango de fechas del dashboard (año/mes) se refleja en la querystring (`?year=2026&month=9`). Permite compartir o recargar una vista concreta sin perder el filtro. Solo frontend, no cambia specs del backend.

### D11 — Caché de `stats` con react-query — CONFIRMADO
- Las queries de `react-query` para las estadísticas del dashboard usan `staleTime` alto (5 min) para no repetir la misma consulta al backend al navegar entre pantallas. Solo frontend, no cambia specs del backend.

### D12 — `insight_settings` fusionado en `user_preferences` — CONFIRMADO
- Se elimina la tabla `insight_settings`; sus tres columnas (`ant_max_amount`, `ant_min_occurrences`, `ant_min_aggregate`) pasan a `user_preferences` (migración `d3a1c9f7e5b2`, con copia de datos existentes). Una sola tabla de "configuración del usuario" en vez de dos.
- Los endpoints `GET/PATCH /insights/settings` no cambian de contrato; solo cambia el almacenamiento interno. `GET/PATCH /users/me/preferences` tampoco expone los campos de insights — siguen siendo dos endpoints con responsabilidades separadas sobre la misma tabla.

### D13 — `over_typical` solo en categorías raíz — CONFIRMADO
- Se mantiene como estaba: la comparación contra la banda de referencia (`over_typical`) solo aplica a categorías raíz. Las subcategorías no tienen banda propia — el histórico suele ser insuficiente para que sea confiable. No requiere cambios.

## Open Questions

(ninguna abierta por ahora)

## Apéndice A — Marcos financieros de referencia

Contenido de dominio tomado de las skills `ailabs-393/ai-labs-claude-skills@finance-manager` (`references/financial_frameworks.md`) y `zph/beancount-skill` (`references/financial_analysis.md`), incorporado como referencia — las skills **no** se instalan. Números tratados como constantes de producto, ajustables sin cambiar specs. (El cambio `budgets-and-savings-goals` reproduce el mismo apéndice, ampliado, en su `design.md` Apéndice C.)

### Tasa de ahorro
`savings_rate = (ingresos − gastos) / ingresos` en el rango consultado (excluye transferencias y borrados). Tramos (`tier`): `<5%` crítico · `5–10%` bajo · `10–20%` medio · `20–30%` bueno · `30–50%` muy bueno · `≥50%` FIRE.

### Bandas objetivo de gasto por categoría (% del gasto total del rango)
Vivienda 25–35 · Transporte 10–20 · Alimentación 10–15 · Suministros 5–10 · Salud 5–10 · Personal/Compras 5–10 · Ocio 5–10.
Señal `over_typical` en la insight de impacto: Vivienda >35 · Transporte >20 · Alimentación >15. Se aplica solo a categorías raíz.

### 50/30/20 (referencia narrativa para el dashboard)
50% necesidades · 30% deseos · 20% ahorro. Útil como marco explicativo junto a la dona por categoría; no se impone ningún cálculo automático en el MVP.
