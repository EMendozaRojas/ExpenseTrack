## 1. Migraciones autocontenidas

- [x] 1.1 `fac793ec36d3`: copiar dentro los datos de la taxonomía original (`eb925b8`) y quitar el import de `app.db.seed_categories`
- [x] 1.2 `b5963a0e5c7c`: copiar dentro los datos de la taxonomía v2 y quitar el import de `app.db.seed_categories`

## 2. Arranque

- [x] 2.1 `docker-compose.yml`: ejecutar `alembic upgrade head` antes de `uvicorn` y montar `alembic.ini`
- [x] 2.2 `Dockerfile`: mismo orden en el `CMD`
- [x] 2.3 README: explicar que las migraciones se aplican solas y cómo lanzarlas a mano

## 3. Test

- [x] 3.1 `env.py`: aceptar una URL inyectada por `config.attributes`
- [x] 3.2 `tests/test_migrations.py`: base vacía → `upgrade head` → esquema, categorías y reglas de sistema correctos → borrar la base

## 4. Verificación

- [x] 4.1 `pytest` en verde
- [x] 4.2 Instalación limpia con un volumen nuevo siguiendo el README: registro 201 y seed de demo correcto
