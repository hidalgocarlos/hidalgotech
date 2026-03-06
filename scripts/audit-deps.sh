#!/bin/bash
# audit-deps.sh — Ejecuta pip-audit sobre todos los requirements.txt del proyecto.
# Criterio de bloqueo: vulnerabilidades conocidas (críticas sin parche = bloquear).
# Uso: ./scripts/audit-deps.sh   o  python -m pip install pip-audit && ./scripts/audit-deps.sh

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v pip-audit &>/dev/null; then
  echo "pip-audit no encontrado. Instalando..."
  python3 -m pip install --quiet pip-audit
fi

FAILED=0
for req in portal/requirements.txt app-*/requirements.txt _template-app/requirements.txt; do
  [ -f "$req" ] || continue
  echo "--- Audit: $req ---"
  if ! pip-audit -r "$req" 2>&1; then
    FAILED=1
  fi
  echo ""
done

if [ "$FAILED" -eq 1 ]; then
  echo "Criterio de bloqueo: no desplegar con vulnerabilidades críticas conocidas sin mitigación."
  echo "Actualiza dependencias (pip install -U ...) o aplica parches antes de hacer release."
  exit 1
fi
echo "Sin vulnerabilidades conocidas en dependencias auditadas."
