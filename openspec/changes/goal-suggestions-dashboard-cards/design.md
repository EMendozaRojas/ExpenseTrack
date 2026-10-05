## Context

Ver `proposal.md` — Why. Separado de `monthly-budgets-planning` el 2026-10-05 por decisión del usuario: las tarjetas del dashboard dependen del modelo final de presupuestos, así que se diseñan e implementan después. Recoge la decisión D9 de `budgets-and-savings-goals` (presets de metas) y la parte del dashboard que estaba diferida.

## Goals / Non-Goals

**Goals:**
- Metas sugeridas explicables (mostrando el cálculo) y editables antes de crear.
- Ver de un vistazo en el dashboard los presupuestos en riesgo y el progreso de las metas.

**Non-Goals:**
- Ritmo de gasto ni recomendaciones de presupuesto en el dashboard (viven en `/budgets`).
- Nuevos endpoints de agregación para el dashboard.

## Decisions

### D1 — Presets de metas: endpoint en backend
- El plan original calculaba los presets en el frontend desde `/stats`, pero ese endpoint no existe. Se crea `GET /goals/suggestions`, que calcula todo en backend y devuelve el `basis` de cada preset.
- Fondo de emergencia: `6 × media de gasto mensual` (3 meses naturales completos anteriores al actual); meses de cobertura = saldos de cuentas no archivadas `cash`/`checking`/`wallet` (reusando el cálculo de saldo existente) / media de gasto mensual; tramo según el Apéndice C de `budgets-and-savings-goals`.
- Independencia financiera: `25 × gasto de los 12 meses naturales completos previos`.
- Sin gasto en la ventana → preset sin `target_amount` y marcado como "sin datos suficientes".
- Frontend: selector "Empezar desde una sugerencia" en el formulario de crear meta, que rellena nombre e importe editables.
- Moneda: una sola moneda por usuario, sin conversión (misma limitación que en presupuestos).

### D2 — Tarjetas del dashboard sin endpoint nuevo
- El frontend reutiliza `GET /budgets?year=&month=` (mes seleccionado en el dashboard) y `GET /goals`, con las mismas query keys de TanStack Query que las páginas de presupuestos y metas para compartir caché.
- Tarjeta de presupuestos: solo los `warning`/`exceeded`, con categoría, `spent`, `amount` del mes y `pct`. Sin sumar montos (padre e hija pueden coexistir, ver D11 de `monthly-budgets-planning`).
- Tarjeta de metas: metas `active` con `current_amount`, `target_amount` y `pct`.

## Risks / Trade-offs

- [Presets que parecen arbitrarios] → `basis` visible en el formulario.
- [Dos peticiones más al abrir el dashboard] → cacheadas y compartidas con las páginas de presupuestos y metas.

## Migration Plan

Sin migraciones ni cambios de infraestructura.

## Open Questions

(ninguna)
