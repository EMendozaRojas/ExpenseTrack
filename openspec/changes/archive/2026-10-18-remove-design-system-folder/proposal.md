## Why

La carpeta `Design System/` (4 imágenes: el logo en varias versiones y `ejemplo.jpg`, la referencia visual) está en la raíz del repo, pero la app no la usa: el frontend sirve solo las copias ligeras `frontend/public/mascota.png` (usada por `BrandMark.tsx`) y `frontend/public/logo.png` (favicon). Mantenerla obliga a una excepción en pre-commit y deja un comentario en el CSS que apunta a una carpeta que nadie consulta.

Acordado con la autora el 2026-10-18: borrar la carpeta entera. Los originales quedan solo en el historial de git.

## What Changes

- Borrar la carpeta `Design System/` completa (`ejemplo.jpg`, `logo con nombre pagina y eslogan.png`, `logo sin fondo listo.png`, `logo sin fondo.png`).
- Quitar la excepción `exclude: ^Design System/` (y su comentario) del hook `check-added-large-files` en `.pre-commit-config.yaml`.
- Reescribir el comentario inicial de `frontend/src/index.css` para que no remita a `Design System/`.
- Los changes archivados que mencionan la carpeta no se editan: son historia.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna: es limpieza del repositorio; no cambia ningún comportamiento de la app ni ningún requisito de las specs)

## Impact

- **Repo**: se elimina `Design System/` (≈ 5 MB de imágenes del árbol de trabajo); `.pre-commit-config.yaml`.
- **Frontend**: solo un comentario en `src/index.css`; `public/mascota.png` y `public/logo.png` no cambian.
- **Pérdida asumida**: ya no hay en el árbol de trabajo el logo con eslogan ni la referencia visual `ejemplo.jpg`; se recuperan con `git show <commit>:"Design System/<archivo>"` si hacen falta.
- **Pendiente**: si en el futuro se cambia la mascota, habrá que partir de una imagen de mayor resolución que ya no estará en el repo (la copia de 600×400 es la única).
