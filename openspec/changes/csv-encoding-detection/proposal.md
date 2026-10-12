<!-- Ficha de idea futura (2026-10-12): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. -->

## Why

La revisión técnica del 2026-10-11 señala que el lector de extractos decodifica con `errors="replace"` (`services/statement_parser.py`): un CSV en latin-1 (habitual en bancos españoles) se importa sin aviso, con caracteres corruptos («CAFETER�A»).

## What Changes

- Probar UTF-8 y, si falla, Windows-1252/latin-1, antes de sustituir caracteres.
- Si ninguna codificación encaja, avisar en la vista previa en vez de importar texto corrupto.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `statement-import`: los extractos en latin-1 se importan con los acentos correctos.

## Impact

- **Backend**: `services/statement_parser.py` y sus tests (CSV de ejemplo en latin-1).
