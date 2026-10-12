## Context

- Los modelos definen `String(n)` y `Numeric(14,2)`, pero casi ningún schema de entrada lo refleja; cuando un valor no cabe, Postgres lanza `DataError` (`StringDataRightTruncation`, `NumericValueOutOfRange`) y FastAPI lo convierte en 500.
- `routers/auth.py` busca el usuario con `User.email == …` tal cual llega, en registro, login y callback de Google.
- `routers/attachments.py` acepta el archivo si `file.content_type` está en `ALLOWED_MIME_TYPES` y sirve la descarga con `Content-Disposition: inline; filename="{nombre}"`. El avatar (`routers/users.py`) usa la misma comprobación de tipo.

## Goals / Non-Goals

**Goals:** ninguna entrada de usuario produce un 500; el registro tiene unas reglas mínimas; los adjuntos son lo que dicen ser y se descargan con cualquier nombre.

**Non-Goals:** política de contraseñas compleja (mayúsculas, símbolos); límite de intentos de login (queda como ficha); antivirus de adjuntos.

## Decisions

### D1 — Límites declarados en el schema
- `app/schemas/limits.py` define `MAX_AMOUNT = Decimal("1e12")` (el máximo de `Numeric(14,2)` es 999.999.999.999,99) y los importes de entrada usan `Field(gt=-MAX_AMOUNT, lt=MAX_AMOUNT, …)`. No se limita el número de decimales: hoy se redondean a 2 al guardar y eso no cambia.
- Cada texto de entrada lleva `max_length` igual al de su columna (`counterparty`, `note` y `pattern` 255; nombres de cuenta y meta 120; nombre de categoría 100; `icon` y `color` 16; `locale` 10; `full_name` 120).
- El tipo de cambio (`Numeric(18,6)`) usa el mismo `MAX_AMOUNT`.
- Así el 422 sale de Pydantic, dice qué campo falla y queda documentado en OpenAPI (`maxLength`, `exclusiveMaximum`).

### D2 — Manejador global de `DataError` como red de seguridad
- `app.add_exception_handler(sqlalchemy.exc.DataError, …)` responde 422 `{"detail": "Los datos no son válidos: algún valor es demasiado largo o está fuera de rango"}` y hace `rollback` implícito (la sesión se cierra al terminar la petición).
- No sustituye a D1: cubre lo que se escape (por ejemplo, campos nuevos sin límite).

### D3 — Contraseña y email
- `UserCreate.password`: `min_length=8`, `max_length=72` (bcrypt solo usa los primeros 72 bytes; con un máximo explícito no hay sorpresas).
- Email normalizado con `strip().lower()` en un validador de `UserCreate`, en el login (`form_data.username`) y en el callback de Google (antes de buscar y al crear la identidad).
- Migración `normalize_user_emails`: `UPDATE users SET email = lower(trim(email))`; antes comprueba que no haya dos emails iguales salvo mayúsculas y, si los hay, falla con un mensaje que los lista (no se fusionan cuentas automáticamente). Lo mismo para `auth_identities.email`.
- Frontend: el formulario de registro valida los 8 caracteres antes de enviar y muestra el mensaje del 422 si llega.

### D4 — Adjuntos
- `app/services/file_signature.py` con `detect_mime(content: bytes) -> str | None` por firma: JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, WebP `RIFF????WEBP`, PDF `%PDF-`. El archivo se acepta si la firma corresponde a un tipo permitido **y** coincide con el declarado; si no, 415 «El contenido del archivo no coincide con su tipo». Se guarda el tipo detectado.
- Mismo control en el avatar (solo imágenes).
- Descarga: `Content-Disposition: inline; filename="<nombre ASCII seguro>"; filename*=UTF-8''<nombre codificado>` (RFC 6266/5987, con `urllib.parse.quote`), y cabecera `X-Content-Type-Options: nosniff`.
- Nombres de más de 255 caracteres: se recorta la base y se conserva la extensión.
- Alternativa descartada: `python-magic`. Necesita `libmagic` en la imagen y solo hay cuatro tipos que reconocer.

## Risks / Trade-offs

- [Un cliente que mande contraseñas de menos de 8 caracteres deja de poder registrarse] → solo afecta a cuentas nuevas; las existentes siguen entrando.
- [Un PNG con una extensión rara pero contenido correcto] → se acepta: lo que cuenta es el contenido.
- [Archivos ya subidos con tipo falso] → no se revisan retroactivamente; se siguen sirviendo con `nosniff`.

## Migration Plan

Migración de datos `normalize_user_emails` (reversible en esquema; los emails no vuelven a su forma original). Regenerar `openapi.json`.

## Open Questions

(ninguna)
