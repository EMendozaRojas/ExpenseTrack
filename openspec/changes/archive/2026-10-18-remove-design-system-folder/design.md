# Design

## Context

Ver `proposal.md` para el motivo. Estado actual:

- `frontend/public/mascota.png` (600×400) es la imagen de la marca; `BrandMark.tsx` la carga con `src="/mascota.png"`.
- `frontend/public/logo.png` (384×256) es el favicon (`frontend/index.html`).
- Ninguna de las dos se genera en el build ni depende de `Design System/`: son archivos estáticos ya versionados.
- `Design System/` solo aparece en `.pre-commit-config.yaml` (excepción del límite de tamaño) y en un comentario de `frontend/src/index.css`. Las specs de `openspec/specs/` no la mencionan.

## Goals / Non-Goals

**Goals:**
- Que el repo no tenga una carpeta de diseño sin uso ni referencias a ella en el código y la configuración.

**Non-Goals:**
- Mover los archivos a otra carpeta (`docs/`, etc.): decidido borrarlos.
- Tocar `mascota.png`, `logo.png` o cualquier componente.
- Reescribir los changes archivados que citan la carpeta.

## Decisions

- **Borrar con `git rm -r`** en vez de ignorar la carpeta en `.gitignore`: los archivos ya están versionados y el objetivo es que desaparezcan del árbol de trabajo; el historial conserva los originales.
- **Quitar la excepción de pre-commit**: sin la carpeta no hace falta, y los archivos de `frontend/public/` pesan menos de 1000 KB (`mascota.png` ≈ 270 KB), así que el hook sigue pasando. Alternativa descartada: dejarla "por si acaso"; una excepción sin motivo confunde.
- **Comentario de `index.css`**: se deja solo lo que sigue siendo cierto (tema "Navy", dark-first, paleta slate de Tailwind) y se elimina la frase que remite a `Design System/`. No se apunta al historial de git en el comentario: es ruido para quien lee el CSS.
- **Changes archivados sin tocar**: documentan lo que se hizo en su momento y son histórico.

## Risks / Trade-offs

- [Se pierde el logo con eslogan y `ejemplo.jpg` del árbol de trabajo] → siguen en el historial de git; se recuperan con `git show <commit>:"Design System/<archivo>"` o `git checkout <commit> -- "Design System"`.
- [La mascota original en 1536×1024 deja de estar en el repo] → la copia de 600×400 es suficiente para el uso actual; si hiciera falta una versión mayor, se parte del historial de git.
- [Una referencia olvidada a la ruta] → comprobar con `grep -rI "Design System"` fuera de `openspec/changes/archive/` y de este change.
