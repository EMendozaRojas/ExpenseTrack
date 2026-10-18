# Tasks

## 1. Limpieza

- [x] 1.1 `git rm -r "Design System"` y comprobar que la carpeta ya no existe (`ls "Design System"` falla) y que `git status` muestra los 4 archivos como borrados
- [x] 1.2 `.pre-commit-config.yaml`: quitar `exclude: ^Design System/` y su comentario del hook `check-added-large-files`; comprobar con `pre-commit run check-added-large-files --all-files` (o, si no está instalado, con `grep -n "Design System" .pre-commit-config.yaml` sin resultados)
- [x] 1.3 `frontend/src/index.css`: quitar del comentario inicial la frase que remite a `Design System/`; comprobar con `docker compose exec frontend npx prettier --check src/index.css`

## 2. Verificación

- [x] 2.1 `grep -rI "Design System" . --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=archive` solo devuelve este change (`openspec/changes/remove-design-system-folder/`)
- [x] 2.2 La app sigue mostrando la mascota y el favicon: `docker compose exec frontend npm test` en verde y `frontend/public/mascota.png` y `logo.png` presentes y sin cambios en `git status`
