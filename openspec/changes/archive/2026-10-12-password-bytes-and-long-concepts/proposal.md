## Why

La segunda revisión técnica (2026-10-12, `informe-ExpenseTrack-v2.md`, 3,65/4) encontró dos hallazgos nuevos 🟢 relacionados con los límites añadidos en `input-validation-limits`:

1. **La contraseña cuenta caracteres, pero bcrypt corta a 72 bytes.** Una contraseña de 72 «ñ» ocupa 144 bytes: se acepta, y luego el login funciona con cualquier otra contraseña que comparta los primeros 72 bytes.
2. **Un concepto de más de 255 caracteres en un CSV tumba toda la importación** con el 422 genérico de la red de seguridad, sin decir qué fila falla.

Acordado con la autora el 2026-10-12: recortar el concepto e importar.

## What Changes

- **Contraseña**: el máximo pasa a ser **72 bytes** en UTF-8 (las letras con acento o la «ñ» cuentan 2), en el backend y en el formulario de registro, con un mensaje que lo explica. El mínimo sigue en 8 caracteres.
- **Extractos**: los conceptos de más de 255 caracteres se recortan a 255 al leer el CSV y la importación sigue normalmente.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `social-auth`: el máximo de la contraseña se mide en bytes.
- `statement-import`: los conceptos largos se recortan en vez de impedir la importación.

## Impact

- **Backend**: `schemas/user.py`, `services/statement_parser.py` y sus tests; `openapi.json` si cambia la descripción.
- **Frontend**: `features/auth/RegisterPage.tsx` y su test.
