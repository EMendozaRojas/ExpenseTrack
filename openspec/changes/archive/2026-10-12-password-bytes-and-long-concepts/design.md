## Context

- `UserCreate.password` usa `max_length=72`, que Pydantic cuenta en caracteres. bcrypt (vía passlib con `bcrypt==4.0.1`) solo usa los primeros 72 **bytes** y descarta el resto sin avisar.
- `parse_csv` guarda la descripción tal cual en `ParsedRow.raw_description`; la columna `import_rows.raw_description` (y `transactions.raw_description`) es `String(255)`, así que un concepto largo provoca `DataError` y el manejador global responde 422 genérico.

## Goals / Non-Goals

**Goals:** ninguna contraseña aceptada se trunca en silencio; un concepto largo no impide importar el extracto.

**Non-Goals:** cambiar de algoritmo de hash (`passlib` sin mantenimiento queda anotado); ampliar la columna a `Text`.

## Decisions

### D1 — Máximo de la contraseña en bytes
- Validador en `UserCreate`: si `len(password.encode("utf-8")) > 72` → 422 «La contraseña puede tener como máximo 72 bytes (las letras con acento o la ñ cuentan doble)». Se quita `max_length=72` (caracteres) para que no haya dos reglas distintas, y la descripción del campo lo explica.
- Frontend: misma regla con `new TextEncoder().encode(password).length` y el mismo mensaje; se quita `maxLength` del `<input>`, porque el navegador cuenta caracteres.

### D2 — Recortar el concepto al leer el CSV
- En `parse_csv`, `description[:255]` (constante `MAX_DESCRIPTION_LENGTH = 255`, alineada con la columna). Se recorta en el lector para que la vista previa, la detección de duplicados (hash y similitud) y el movimiento final usen el mismo texto.
- Alternativa descartada (decisión de la autora): rechazar el archivo indicando la fila. El extracto lo genera el banco y editarlo a mano es incómodo; 255 caracteres bastan para reconocer el movimiento.

## Risks / Trade-offs

- [Dos conceptos que solo difieren después del carácter 255] → se verían iguales; en la práctica los bancos no generan conceptos tan largos y casi idénticos.

## Migration Plan

Sin migraciones.

## Open Questions

(ninguna)
