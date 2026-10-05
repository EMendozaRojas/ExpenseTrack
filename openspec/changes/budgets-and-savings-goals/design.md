## Context

Ver `proposal.md` — Why. Depende de `accounts-and-transactions` y `hierarchical-categories-and-rules`.

> **Revisión 2026-10-05 — alcance recortado al MVP implementado.** Las decisiones marcadas **DIFERIDO** no se implementaron en este change y pasan a `monthly-budgets-planning` (presupuestos) y `goal-suggestions-dashboard-cards` (metas sugeridas y dashboard); se conserva su razonamiento como punto de partida. Las marcadas **AJUSTADO** describen cómo quedó en el código cuando difiere de lo decidido inicialmente.

## Goals / Non-Goals

**Goals:**
- Topes de gasto por categoría con estado mensual y avisos 80/100% sin duplicados por mes.
- Metas de ahorro con seguimiento, aportaciones y proyección.

**Non-Goals:**
- Presupuestos por periodo distinto de mensual (semanal/anual) — posible ampliación posterior.
- Notificaciones push.
- Recomendaciones con ML.
- (Diferido) rollover, alertas persistidas en tabla propia, scheduler, recomendaciones, presets de metas y cards del dashboard.

## Decisions

> Estado de la revisión (2026-09-02): D1–D8 resueltas. D9 (presets de metas) añadida al incorporar los marcos financieros del Apéndice C. Revisión 2026-10-05: D2, D3, D4, D6, D9 diferidas; D1, D8, D10 ajustadas al código.

### D1 — Alcance de un presupuesto — DECIDIDO: cualquier nivel
- Se puede crear un presupuesto sobre **cualquier categoría de gasto visible** (raíz o subcategoría).
- `spent(budget, mes)` = suma de los gastos del usuario en el mes que caen en el **subárbol** de la categoría del presupuesto: para una raíz = la raíz + sus subcategorías; para una subcategoría = solo ella. Excluye transferencias y borrados.
- Cada presupuesto se evalúa y se muestra en su propia fila, **de forma independiente**. Si el usuario pone tope en una raíz y otro en una de sus hijas, el gasto de la hija cuenta en ambos: es decisión suya, no se impide ni se avisa. No se suman presupuestos entre sí en ningún sitio, así que no hay doble conteo real.
- Unicidad: como máximo un presupuesto activo por `(owner_id, category_id, period, starts_on)`.
- **AJUSTADO (2026-10-05):** sin `period` ni `starts_on`, la unicidad es **un presupuesto por `(owner_id, category_id)`**, comprobada en el endpoint (409). El presupuesto es recurrente: una sola fila se evalúa contra cualquier mes consultado. `spent` excluye borrados y lo que no sea `direction = 'expense'`.

### D2 — Moneda del presupuesto — DIFERIDO
- No implementado: el presupuesto no tiene `currency` y `spent` suma todos los gastos de la categoría sin filtrar por moneda.
- El presupuesto tiene `currency` (default `EUR`). `spent` suma **solo** movimientos en esa moneda. Los gastos de la categoría en otra moneda se listan aparte (informativo), sin convertir. La conversión llega con `multicurrency-social-auth-attachments`.

### D3 — `rollover` — DIFERIDO (decidido originalmente: implementación completa en el MVP)
- Campo `rollover boolean` en `budgets` (default `false`).
- **Tope efectivo** del mes M:
  - `carryover(M) = 0` si M es el primer mes ≥ `starts_on`.
  - `carryover(M) = max(0, tope_efectivo(M-1) − spent(M-1))` en otro caso (solo si `rollover=true`; si es `false`, `carryover(M)=0` siempre).
  - `tope_efectivo(M) = amount + carryover(M)`. Como `carryover ≥ 0`, el tope efectivo nunca baja de `amount` (no se arrastra deuda por sobregasto).
- `pct`, `status` y las alertas 80/100% se calculan contra **`tope_efectivo`**, no contra `amount`.
- La respuesta de `GET /budgets?month=` expone `amount` (base), `carryover` y `effective_amount` además de `spent`/`pct`/`status`.
- **`amount` y `rollover` son valores vigentes únicos** (no versionados por mes): la recursión desde `starts_on` usa el `amount` y el `rollover` actuales para todos los meses. Consecuencia conocida: activar `rollover` "acredita" retroactivamente todo el infragasto desde `starts_on`; para resetear, el usuario mueve `starts_on` al mes en curso. Aceptable para una herramienta personal; documentarlo en la UI.
- Coste: la recursión recorre `[starts_on, mes_consultado]` haciendo un `spent()` por mes (query barata con índice `(owner_id, posted_at)`); memoización por `(budget_id, mes)` dentro de la petición.

### D4 — Job diario — DIFERIDO (decidido originalmente: servicio `scheduler` en docker-compose)
- **Implementado en su lugar (2026-10-05):** no hay scheduler ni tabla `budget_alerts`. `app/services/notifications.py::check_budget_notifications` se llama de forma síncrona tras **crear y editar** un movimiento; evalúa los presupuestos activos del mes en curso y crea notificaciones `budget_warning`/`budget_exceeded` únicas por `(owner, type, budget_id, period_key=YYYY-MM)`. No se dispara al borrar movimientos ni en el commit de imports.

Decisión original, para el change diferido:
- Nuevo service `scheduler` en `docker-compose.yml`, `command: python -m app.jobs.scheduler`, misma imagen y env que `backend`, `depends_on: db`.
- Usa APScheduler (`BlockingScheduler`, es su propio proceso) para ejecutar `reconcile_budgets` 1×/día (03:00). El mismo scheduler alojará más adelante el fetch de tasas FX (`multicurrency…`) y la detección de recurrentes (`visual-dashboard…`).
- `reconcile_budgets`: recorre presupuestos activos cuyo mes en curso pueda tener alertas pendientes; recalcula `spent`/`tope_efectivo` y crea las `budget_alerts` que falten (idempotente por `UNIQUE(budget_id, period_month, threshold)`). Es solo red de seguridad: el disparo normal es síncrono.
- Disparo síncrono: el servicio que crea/edita/borra un `transaction` y el commit de `imports` recalculan las `(categoría→presupuestos afectados, mes)` una sola vez y crean las alertas que crucen umbral.

### D5 — Cortes de `status` — CONFIRMADO
- `ok` (`pct` < 80), `warning` (80 ≤ `pct` < 100), `exceeded` (`pct` ≥ 100). `pct = spent / effective_amount`, puede pasar de 100.
- **AJUSTADO (2026-10-05):** sin rollover, `pct = spent / amount × 100`, redondeado a 1 decimal.

### D6 — Algoritmo de recomendación — DIFERIDO (decidido originalmente: media de 3 meses + banda 10% + sugerir crear)
- Ventana: los **3 meses naturales completos** anteriores al actual (se excluye el mes en curso, parcial).
- Por categoría de gasto (subárbol para raíces): `meses_con_gasto` = los de esos 3 con `spent > 0`.
- Si `len(meses_con_gasto) < 2` → no se recomienda nada para esa categoría (señal insuficiente).
- `sugerido = round(media(spent de meses_con_gasto))`.
- Categoría **con** presupuesto activo: comparar `sugerido` con `amount` (base). Banda muerta ±10%: `abs(sugerido − amount) / amount ≤ 0.10` → `keep`; si no, `raise` / `lower`.
- Categoría **sin** presupuesto: si `len(meses_con_gasto) == 3` (gasto consistente), sugerir **crear** un presupuesto con `amount = sugerido`.
- La respuesta incluye `basis`: los 3 valores mensuales de `spent` y su media, para que la UI muestre el "por qué".
- Enriquecimiento con los marcos de referencia (Apéndice C): `basis` incluye además `share_pct` (share de la categoría sobre el gasto total del rango) y `over_typical` (`true` si `share_pct` supera la banda de referencia de esa categoría — Vivienda >35, Transporte >20, Alimentación >15). Es informativo para el "por qué" de la recomendación; no cambia los flags `raise/lower/keep/create`.

### D7 — `current_amount` de la meta — CONFIRMADO: Opción A
- `current_amount` = suma de `goal_contributions`. Nada más. `linked_account_id` se guarda pero es **solo informativo** en el MVP (no deriva saldo). La derivación desde el saldo de la cuenta (Opción B) queda para un cambio posterior.

### D8 — Proyección de la meta — CONFIRMADO
- Ritmo = media de aportaciones por mes de los **últimos 3 meses** naturales con aportación.
- `fecha_estimada = primer_día_mes_actual + ⌈(target − current) / ritmo⌉ meses`.
- Si ritmo ≤ 0, o hay < 2 meses con aportación → se devuelve "sin ritmo suficiente para estimar", no una fecha.
- **AJUSTADO (2026-10-05):** `ritmo = total aportado en los 3 meses completos anteriores al actual / nº de esos meses`, contando solo meses desde el mes de creación de la meta (los meses sin aportación cuentan como 0). `fecha_estimada = hoy + ⌈(target − current) / ritmo⌉ meses`. Si no ha pasado ningún mes completo desde la creación o el ritmo es 0 → "sin datos suficientes". Si ya se alcanzó el objetivo → 0 meses restantes.
- Estado de la meta: `active` / `completed` / `archived` (en vez de `reached`); pasa a `completed` automáticamente al alcanzar el objetivo con una aportación.

### D9 — Presets de metas de ahorro — DIFERIDO (decidido originalmente: prefill en el frontend con los marcos del Apéndice C)
- El flujo "crear meta" del frontend ofrece dos presets, calculados en cliente a partir de `/stats` (sin endpoint nuevo en el MVP):
  - **Fondo de emergencia**: `target_amount = 6 × media(gasto mensual de los 3 meses completos previos)`. La UI muestra los meses de cobertura actuales (`activos_líquidos / gasto_mensual_medio`, con `activos_líquidos` = suma de saldos de cuentas `type IN ('cash','checking','wallet')`) y su tramo (Apéndice C).
  - **Independencia financiera (FI)**: `target_amount = 25 × gasto_anual` (regla del 4%).
- Son sugerencias editables; el usuario ajusta el importe. El backend no valida contra estos números.
- Un endpoint `GET /goals/suggestions` que devuelva estos presets ya calculados queda como mejora posterior (ver Open Questions).

## Risks / Trade-offs

- [Presupuesto en raíz y en subcategoría a la vez] → permitido y no se avisa (D1); como no se suman presupuestos entre sí, no hay incoherencia; cada uno se computa sobre su subárbol.
- [Avisos que no se disparan al borrar movimientos ni al importar] → aceptado en el MVP; el estado en `GET /budgets` siempre es correcto porque se calcula al vuelo. Se resuelve en el change diferido.
- [Gastos en otra moneda suman al presupuesto sin convertir] → aceptado mientras el uso sea mayoritariamente en EUR; se resuelve con `currency` en el change diferido.
- Riesgos de rollover, recomendaciones y scheduler: ver el change diferido.

## Migration Plan

1. Migraciones de esquema implementadas: `budgets` (`owner_id`, `category_id`, `amount`, `is_active`, `created_at`) y `savings_goals` + `goal_contributions`.
2. Sin data-migration.
3. Rollback: `downgrade` elimina las tablas nuevas.

### D10 — Canal de entrega de alertas — AJUSTADO
- Decisión original: solo aviso dentro de la app, sin email.
- **Implementado (2026-10-05):** aviso in-app mediante el sistema de notificaciones (badge de no leídas) **y además** envío de email best-effort con `app/services/email.py`. En local apunta a Mailhog (nunca entrega a internet); con `smtp_host` vacío el envío se omite sin errores.

## Open Questions

- Todas las preguntas abiertas (versionado de `amount`/`rollover`, `GET /goals/suggestions`, alcance de `over_typical`) pasan a los changes diferidos `monthly-budgets-planning` (presupuestos) y `goal-suggestions-dashboard-cards` (metas sugeridas y dashboard).

## Apéndice C — Marcos financieros de referencia

Contenido de dominio tomado de las skills `ailabs-393/ai-labs-claude-skills@finance-manager` (`references/financial_frameworks.md`) y `zph/beancount-skill` (`references/financial_analysis.md`), incorporado como referencia — las skills **no** se instalan. Estos números son constantes de producto, ajustables sin cambiar specs.

### Tasa de ahorro
`tasa_ahorro = (ingresos − gastos) / ingresos` en el rango. Tramos: `<5%` crítico · `5–10%` bajo · `10–20%` medio · `20–30%` bueno · `30–50%` muy bueno · `≥50%` FIRE.

### Reparto 50/30/20
50% necesidades (vivienda, suministros, alimentación, transporte, seguros) · 30% deseos (restauración, ocio, compras, aficiones) · 20% ahorro + amortización de deuda.

### Reparto objetivo por categoría (% del gasto total)
Vivienda 25–35 · Transporte 10–20 · Alimentación 10–15 · Suministros 5–10 · Salud 5–10 · Personal/Compras 5–10 · Ocio 5–10 · Ahorro ≥20.
Señal `over_typical`: Vivienda >35 · Transporte >20 · Alimentación >15.

### Fondo de emergencia
`meses_cubiertos = activos_líquidos / gasto_mensual_medio`, con `activos_líquidos` = suma de saldos de cuentas `type IN ('cash','checking','wallet')`. Tramos: `<1` crítico · `1–3` mínimo · `3–6` adecuado (empleo estable) · `6–12` fuerte · `12+` excepcional. Objetivo recomendado para la meta "Fondo de emergencia": 3–6 × gasto mensual medio (el preset D9 usa 6×).

### Número de independencia financiera (FI)
`FI = gasto_anual × 25` (regla del 4% de retirada segura). Preset D9 de `target_amount` para una meta a largo plazo.

### Deuda / ingresos
`ratio = pagos_mensuales_de_deuda / ingreso_bruto_mensual`. `<20` excelente · `20–36` aceptable · `36–43` preocupante · `>43` crítico. **Fuera de alcance del MVP**: la app no modela deuda todavía; referencia para cuando exista el concepto de préstamo/pasivo.

### Orden de prioridad de objetivos
Referencia para el orden en que la UI sugiere/ordena metas: 1) necesidades básicas · 2) mínimos de deuda · 3) fondo de emergencia inicial · 4) aportación que iguala la empresa · 5) deuda cara (>7%) · 6) jubilación adicional · 7) otras metas de ahorro · 8) deuda barata (<4%) · 9) inversión adicional.
