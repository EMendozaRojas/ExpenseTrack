## 1. Backend

- [x] 1.1 `ACCOUNT_TYPES` y `AccountType` con `general`; `AccountCreate.type` opcional con `general` por defecto y descripción actualizada
- [x] 1.2 Test: crear una cuenta sin tipo la guarda como `general`
- [x] 1.3 Regenerar `backend/openapi.json`

## 2. Frontend

- [x] 2.1 `TransactionsPage`: texto de ejemplo "Mi cuenta" y sin enviar `type`; `AccountType` y `AccountInput` con `type` opcional/`general`
- [x] 2.2 Test del formulario "Crea tu primera cuenta"

## 3. Coherencia

- [x] 3.1 `goal-suggestions-dashboard-cards`: incluir `general` en las cuentas que cuentan como activos líquidos

## 4. Verificación

- [x] 4.1 Suites de backend y frontend en verde; `ruff`/`mypy` sin avisos nuevos
