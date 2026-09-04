#!/usr/bin/env bash
# Wrapper para correr el CLI de openspec sin tener Node instalado en el host.
# Uso: ./scripts/openspec.sh <comando> [args...]
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME="$HOME" \
  -e npm_config_cache=/tmp/npm-cache \
  -v "$HOME/.config:$HOME/.config" \
  -v "$PROJECT_DIR:/workspace" \
  -w /workspace \
  node:22-alpine \
  npx --yes @fission-ai/openspec@latest "$@"
