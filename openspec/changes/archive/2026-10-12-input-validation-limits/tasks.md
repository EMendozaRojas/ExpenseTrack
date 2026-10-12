## 1. Límites de entrada

- [x] 1.1 `app/schemas/limits.py` con `MAX_AMOUNT`; importes de entrada acotados en transacciones, transferencias, cuentas, presupuestos, metas, aportaciones y tipos de cambio
- [x] 1.2 `max_length` en los textos de entrada según su columna
- [x] 1.3 Manejador global de `DataError` → 422

## 2. Registro

- [x] 2.1 `UserCreate`: contraseña 8–72 caracteres; email en minúsculas
- [x] 2.2 Login y callback de Google con el email normalizado
- [x] 2.3 Migración `normalize_user_emails` con comprobación de conflictos
- [x] 2.4 Frontend: el registro avisa del mínimo de 8 caracteres

## 3. Adjuntos y avatar

- [x] 3.1 `services/file_signature.py`; adjuntos y avatar comprueban la firma del contenido
- [x] 3.2 Descarga con `filename*=UTF-8''…` y `X-Content-Type-Options: nosniff`
- [x] 3.3 Nombres de más de 255 caracteres recortados conservando la extensión

## 4. Tests y docs

- [x] 4.1 Tests: textos largos e importes enormes dan 422; `DataError` da 422; contraseña corta y email con mayúsculas; adjunto con nombre unicode, con tipo falso y con nombre largo; avatar con tipo falso
- [x] 4.2 Regenerar `openapi.json`

## 5. Verificación

- [x] 5.1 `pytest`, `tsc`, `eslint` y `vitest` en verde
- [x] 5.2 Repetir los casos 500 del informe: ahora 422/415/200 (tests HTTP contra Postgres en `test_input_validation.py`)
