## 1. Aislamiento

- [ ] 1.1 `conftest.py`: fijar `DATABASE_URL` (base `_test`) y `SMTP_HOST=""` antes de importar la app
- [ ] 1.2 `conftest.py`: fixture de sesión que recrea la base de tests y aplica `alembic upgrade head`
- [ ] 1.3 `tests/test_isolation.py`: guarda de base `_test` y SMTP desactivado

## 2. Docs

- [ ] 2.1 README (Tests): los tests usan su propia base y no envían correo

## 3. Verificación

- [ ] 3.1 `pytest` en verde
- [ ] 3.2 Tras `pytest`, Mailhog sin emails nuevos y la secuencia de `users` de desarrollo sin cambios
