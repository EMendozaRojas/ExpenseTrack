## Context

- `DashboardPage`: el selector de cuenta solo se pinta con `accounts.length > 1`.
- `TransactionForm`: siempre pinta el `<select>` «Cuenta»; un efecto elige la primera cuenta si no hay ninguna seleccionada.
- `ImportsPage`: siempre pinta el `<select>` con la opción vacía «Selecciona una cuenta»; `accountId` empieza en `null` y el botón de subir está deshabilitado hasta elegir.
- Usuario demo (id 1779): «Cuenta Principal» (1110, principal, 141 movimientos) y «Cuenta Secundaria» (2043, ahorro, 18 movimientos de agosto a octubre de 2026, sin importaciones, metas vinculadas ni adjuntos).

## Goals / Non-Goals

**Goals:** con una sola cuenta, ningún formulario pregunta por ella; con varias, todo sigue igual.

**Non-Goals:** pantalla de cuentas (`accounts-screen`); cambios en el backend; cambiar cómo se elige la cuenta cuando hay varias.

## Decisions

### D1 — Misma regla que el dashboard: `accounts.length > 1`
- `TransactionForm`: el par etiqueta + `<select>` solo se pinta con más de una cuenta; el efecto que elige la primera cuenta ya cubre el caso de una sola.
- `ImportsPage`: con exactamente una cuenta, `accountId` toma esa cuenta automáticamente (efecto al cargar las cuentas) y no se pinta el `<select>`; con varias, se mantiene «Selecciona una cuenta».
- Alternativa descartada: mostrar el nombre de la cuenta como texto fijo. No aporta información con una sola cuenta.

### D2 — Datos del demo con SQL puntual, no con migración
- Es un ajuste de datos de prueba de un solo usuario en la base de desarrollo, no un cambio de esquema: `UPDATE transactions SET account_id = 1110 … WHERE account_id = 2043 AND owner_id = 1779` (las columnas de moneda coinciden: ambas cuentas en EUR) y `DELETE FROM accounts WHERE id = 2043`, en una transacción y tras una copia de seguridad.
- El script `seed_demo_data.py` ya crea una sola cuenta: no hace falta cambiarlo.

## Risks / Trade-offs

- [Los saldos por cuenta del demo cambian] → el total y las cifras del dashboard con «Todas las cuentas» son los mismos; el saldo de «Cuenta Principal» sube por los movimientos traspasados.

## Migration Plan

Sin migraciones de esquema. Copia de seguridad de la base de desarrollo antes del ajuste del demo.

## Open Questions

(ninguna)
