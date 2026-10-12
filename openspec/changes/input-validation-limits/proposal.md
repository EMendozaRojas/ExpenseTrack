## Why

La revisión técnica del 2026-10-11 (`informe-ExpenseTrack.md`, hallazgos 🟡) encontró entradas que tumban la API con un **500** en vez de rechazarse con un **422**, y huecos de validación en el registro y los adjuntos:

- `counterparty` de 300 caracteres, nombre de meta de 1000 caracteres o importe de `-10¹⁵` → 500 (la base rechaza el valor porque los schemas no tienen los límites de las columnas). Solo hay 2 `max_length` en todos los schemas.
- Descargar un adjunto llamado `recibo_日本.png` → 500 (`UnicodeEncodeError` en la cabecera), y el nombre permite inyectar comillas en la cabecera.
- El tipo de un adjunto se toma de lo que dice el navegador: se acepta un HTML declarado como `image/png`. Tampoco se envía `X-Content-Type-Options: nosniff`.
- El registro acepta la contraseña `""` y trata `ANA@…` y `ana@…` como dos cuentas distintas.

Acordado con la autora el 2026-10-12, con contraseña mínima de 8 caracteres.

## What Changes

- **Límites en los schemas de entrada**, alineados con las columnas: textos con `max_length` y los importes acotados a lo que cabe en `Numeric(14,2)` (menos de un billón en valor absoluto). Superarlos da 422 con el campo señalado.
- **Red de seguridad global**: si un valor llega igualmente a la base y esta lo rechaza por tamaño o formato (`DataError`), la API responde 422 «Los datos no son válidos» en vez de 500.
- **Registro**: contraseña de 8 a 72 caracteres; email siempre en minúsculas y sin espacios al registrarse, al iniciar sesión y al entrar con Google. Una migración pasa a minúsculas los emails existentes.
- **Adjuntos y avatar**:
  - Descarga con el nombre codificado según el estándar (`filename*=UTF-8''…`), con cualquier carácter.
  - Se comprueba que el contenido es de verdad JPEG, PNG, WebP o PDF mirando sus primeros bytes («firma»); si no coincide, 415.
  - Las descargas llevan `X-Content-Type-Options: nosniff`.
  - Nombres de más de 255 caracteres se recortan conservando la extensión.

## Capabilities

### New Capabilities

- `input-validation`: los datos inválidos se rechazan con 422, nunca con un error interno.

### Modified Capabilities

- `social-auth`: reglas de contraseña y normalización del email.
- `receipt-attachments`: nombres con cualquier carácter y comprobación del contenido real.

## Impact

- **Backend**: `app/schemas/*` (nuevo `app/schemas/limits.py`), `app/main.py` (manejador de `DataError`), `routers/auth.py`, `routers/attachments.py`, `routers/users.py` (avatar), nuevo `app/services/file_signature.py`, migración nueva para los emails, `openapi.json` regenerado.
- **Frontend**: el formulario de registro pide 8 caracteres como mínimo (mensaje antes de enviar).
- **Datos**: los emails existentes pasan a minúsculas (en la base de desarrollo no hay ninguno con mayúsculas ni conflictos).
