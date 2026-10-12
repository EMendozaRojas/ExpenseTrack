## 1. Aislamiento

- [x] 1.1 `conftest.py`: fijar `DATABASE_URL` (base `_test`) y `SMTP_HOST=""` antes de importar la app
- [x] 1.2 `conftest.py`: fixture de sesión que recrea la base de tests y aplica `alembic upgrade head`
- [x] 1.3 `tests/test_isolation.py`: guarda de base `_test` y SMTP desactivado

## 2. Docs

- [x] 2.1 README (Tests): los tests usan su propia base y no envían correo

## 3. Verificación

- [x] 3.1 `pytest` en verde
- [x] 3.2 Tras `pytest`, Mailhog sin emails nuevos y la secuencia de `users` de desarrollo sin cambios
