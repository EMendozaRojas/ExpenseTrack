## Why

En el MVP un usuario solo puede crear su primera cuenta desde la app, pero dos formularios preguntan igualmente por la cuenta: «Agregar movimiento» muestra un desplegable «Cuenta» con una sola opción, e «Importar estado de cuenta» empieza en «Selecciona una cuenta» y obliga a elegir esa única cuenta antes de importar. El selector «Todas las cuentas» del dashboard ya se oculta con una sola cuenta; se vio en las pruebas porque el usuario demo tiene una segunda cuenta creada fuera de la app. Revisado y acordado con la autora el 2026-10-09.

## What Changes

- **Una sola regla para los tres sitios**: el campo de cuenta solo aparece cuando el usuario tiene más de una cuenta; con una, se usa esa cuenta automáticamente.
  - «Agregar movimiento»: sin campo «Cuenta» con una sola cuenta.
  - «Importar estado de cuenta»: sin campo «Cuenta» con una sola cuenta, y se puede importar directamente.
  - Dashboard: el selector ya cumple la regla (sin cambios).
- **Datos del usuario demo** (`demo.datos@example.com`): sus 18 movimientos de «Cuenta Secundaria» pasan a «Cuenta Principal» y la cuenta secundaria, ya vacía, se elimina, para que se vea como un usuario real del MVP. Las cifras del dashboard no cambian.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `transactions`: el formulario de movimiento y el de importación solo piden la cuenta si hay varias.

## Impact

- **Frontend**: `features/transactions/components/TransactionForm.tsx`, `features/imports/ImportsPage.tsx` y sus tests.
- **Backend**: sin cambios.
- **Datos**: ajuste puntual del usuario demo en la base de datos de desarrollo (no es una migración: no afecta a otros usuarios).
- **Relación**: cuando se implemente `accounts-screen`, los campos reaparecen solos al crear una segunda cuenta.
