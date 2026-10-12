## 1. Dependencias

- [x] 1.1 Backend: `fastapi` 0.143.0, `python-multipart` 0.0.32, `PyJWT[crypto]` 2.15.1 en vez de `python-jose`; `pip-audit` en `requirements-dev.txt`
- [x] 1.2 Código: PyJWT en `security.py` y `google_oauth.py`; constantes HTTP 413/422 renombradas; test de documentación con `contentMediaType`; `openapi.json` regenerado
- [x] 1.3 Frontend: `npm audit fix`; `vitest` y `@vitest/coverage-v8` 5.0.4
- [x] 1.4 `pip-audit` y `npm audit` sin vulnerabilidades

## 2. Calidad

- [x] 2.1 `ruff check --fix` y `ruff format` en todo `backend/`; partir las líneas largas que quedan
- [x] 2.2 Corregir los 6 errores de `mypy app`
- [x] 2.3 Prettier en todo `frontend/`
- [x] 2.4 `logo.png` a 384×256

## 3. Hooks y CI

- [x] 3.1 `.pre-commit-config.yaml`: mypy, ESLint y Prettier vía `docker compose exec`; excluir `Design System/` del límite de tamaño
- [x] 3.2 `.github/workflows/ci.yml` con los jobs de backend y frontend
- [x] 3.3 README y `BUENAS_PRACTICAS.md`: cómo instalar los hooks y qué comprueba el CI

## 4. Verificación

- [x] 4.1 `pre-commit run --all-files` equivalente en verde (ruff, formato, mypy, ESLint, Prettier, pytest, vitest, build)
- [x] 4.2 La autora instala `pre-commit` y los hooks; el primer push a GitHub muestra el CI en verde
