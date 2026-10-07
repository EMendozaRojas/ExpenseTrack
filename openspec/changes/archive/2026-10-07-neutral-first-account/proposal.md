## Why

Al crear la primera cuenta desde Movimientos, el formulario solo pide nombre y si es la principal, pero el campo de nombre muestra "Efectivo" como ejemplo y la app guarda la cuenta como de tipo efectivo (`cash`) sin que el usuario lo elija. Para el MVP la primera cuenta debe ser simplemente "una cuenta", sin tipo: ni el texto ni el dato guardado deben decir algo que el usuario no ha elegido.

## What Changes

- El ejemplo del campo Nombre pasa de "Efectivo" a **"Mi cuenta"**.
- Nuevo tipo de cuenta **`general`** ("sin especificar") y `type` pasa a ser opcional al crear una cuenta, con `general` por defecto. El frontend deja de enviar el tipo.
- Las cuentas existentes no cambian (no se puede distinguir una cuenta de efectivo real de una creada así).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `accounts`: el tipo de cuenta es opcional y por defecto `general`.

## Impact

- **Backend**: `app/models/account.py` (`ACCOUNT_TYPES`), `app/schemas/account.py` (tipo opcional, descripción); `backend/openapi.json` regenerado.
- **Frontend**: `features/transactions/TransactionsPage.tsx` (texto de ejemplo, sin `type`), `features/transactions/types.ts`.
- **Datos**: sin migración (el tipo es texto sin restricción en la base de datos).
- **Relación**: `goal-suggestions-dashboard-cards` cuenta como "activos líquidos" las cuentas `cash`/`checking`/`wallet`; debe incluir también `general`.
