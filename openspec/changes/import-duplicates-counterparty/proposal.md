<!-- Ficha de idea futura (2026-10-12): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. -->

## Why

La revisión técnica del 2026-10-11 detectó que la detección de duplicados al importar un extracto compara el texto solo con `raw_description` y `note` (`services/reconciler.py`), no con `counterparty`. Un movimiento creado por la API con `counterparty` no se reconoce como duplicado. Desde la app no pasa, porque el formulario guarda el texto en `note`.

## What Changes

- Incluir `counterparty` en la comparación de texto de los duplicados probables.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `statement-import`: la detección de duplicados tiene en cuenta la contraparte.

## Impact

- **Backend**: `services/reconciler.py` y sus tests.
