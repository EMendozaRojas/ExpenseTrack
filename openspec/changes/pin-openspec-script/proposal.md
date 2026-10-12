<!-- Ficha de idea futura (2026-10-12): solo propuesta, no se implementa durante el MVP. Specs, design y tareas se escriben cuando se decida implementarla. -->

## Why

La revisión técnica del 2026-10-11 señala que `scripts/openspec.sh` ejecuta `npx @fission-ai/openspec@latest` (una versión sin fijar) en un contenedor que monta `$HOME/.config` del host. Una versión nueva y maliciosa o con cambios incompatibles se ejecutaría con acceso a la configuración del usuario.

## What Changes

- Fijar la versión de OpenSpec en el script.
- Montar solo lo necesario (el repositorio), no `$HOME/.config`.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna: es tooling de desarrollo)

## Impact

- **Repo**: `scripts/openspec.sh`.
