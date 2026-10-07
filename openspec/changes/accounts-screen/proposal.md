<!-- Ficha de idea futura (2026-10-07): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. -->

## Why

La app solo permite crear la primera cuenta (el formulario "Crea tu primera cuenta" de Movimientos aparece únicamente cuando no hay ninguna). Después no hay ningún sitio para añadir otra cuenta, cambiarle el nombre, marcar cuál es la principal o archivarla, aunque el backend ya lo permite (`/accounts`). Sin esto no se pueden usar de verdad varias cuentas: el desplegable de cuentas del dashboard, las cuentas en otra moneda o el detalle por cuenta en los presupuestos quedan fuera del alcance del usuario.

## What Changes

- Nueva pantalla **Cuentas** (por ejemplo, dentro de Configuración) con la lista de cuentas y el saldo de cada una.
- **Crear** más cuentas con nombre, tipo (opcional, `general` por defecto), moneda y saldo inicial.
- **Editar** el nombre y marcar cuál es la **principal** (solo puede haber una).
- **Archivar** una cuenta que ya no se use, con un aviso de que sus movimientos se conservan.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `accounts`: añade la gestión de cuentas desde el frontend (el backend ya cumple la spec; desarchivar no existe hoy y habría que decidir si se añade).

## Impact

- **Frontend**: nuevo `features/accounts/` y entrada en Configuración o en el menú.
- **Backend**: sin cambios previstos, salvo que se quiera desarchivar.
- **Relación**: es un requisito previo de `independent-currency-accounts` (crear la cuenta en otra moneda) y de `budget-spending-by-account` (tener varias cuentas que desglosar).
