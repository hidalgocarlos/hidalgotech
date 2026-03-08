#!/bin/bash
# check-server.sh — Comprueba en el servidor qué falta para hidalgotech
# Ejecutar en el servidor: bash check-server.sh   (desde la raíz del proyecto o desde $HOME)

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Buscar raíz del proyecto (donde está este script o donde está un docker-compose.yml)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/docker-compose.local.yml" ]; then
  ROOT="$SCRIPT_DIR"
else
  ROOT="${HOME}/hidalgotech"
  if [ ! -f "$ROOT/docker-compose.local.yml" ]; then
    echo "No se encuentra el proyecto (ni en $(dirname "$SCRIPT_DIR") ni en $ROOT)."
    echo "Clona el repo primero: git clone https://github.com/hidalgocarlos/hidalgotech.git $ROOT"
    exit 1
  fi
fi

echo "=== Comprobando servidor (proyecto en $ROOT) ==="
echo ""

MISSING=0

# 1. Git
if command -v git &>/dev/null; then
  echo -e "${GREEN}[OK]${NC} Git instalado: $(git --version)"
else
  echo -e "${RED}[FALTA]${NC} Git no instalado."
  echo "  → sudo apt update && sudo apt install -y git"
  MISSING=$((MISSING + 1))
fi

# 2. Docker
if command -v docker &>/dev/null; then
  echo -e "${GREEN}[OK]${NC} Docker instalado: $(docker --version)"
else
  echo -e "${RED}[FALTA]${NC} Docker no instalado."
  echo "  → Ejecuta: sudo ./setup-server.sh   (o instala Docker según DEPLOY.md)"
  MISSING=$((MISSING + 1))
fi

# 3. Docker Compose (plugin)
if docker compose version &>/dev/null 2>&1; then
  echo -e "${GREEN}[OK]${NC} Docker Compose: $(docker compose version --short 2>/dev/null || docker compose version)"
else
  echo -e "${RED}[FALTA]${NC} Docker Compose (plugin) no disponible."
  echo "  → sudo apt install -y docker-compose-plugin"
  MISSING=$((MISSING + 1))
fi

# 4. Red Docker 'proxy'
if command -v docker &>/dev/null && docker network inspect proxy &>/dev/null 2>&1; then
  echo -e "${GREEN}[OK]${NC} Red Docker 'proxy' existe."
else
  echo -e "${RED}[FALTA]${NC} Red Docker 'proxy' no existe."
  echo "  → docker network create proxy"
  MISSING=$((MISSING + 1))
fi

# 5. .env
if [ -f "$ROOT/.env" ]; then
  echo -e "${GREEN}[OK]${NC} Archivo .env existe."
  if grep -q "SECRET_KEY=CHANGE_THIS" "$ROOT/.env" 2>/dev/null || grep -q "SECRET_KEY=$" "$ROOT/.env" 2>/dev/null; then
    echo -e "  ${YELLOW}[AVISO]${NC} SECRET_KEY sigue por defecto. Genera una: openssl rand -hex 32"
  fi
else
  echo -e "${RED}[FALTA]${NC} No existe .env en la raíz del proyecto."
  echo "  → cp $ROOT/.env.example $ROOT/.env   y edita: nano $ROOT/.env"
  MISSING=$((MISSING + 1))
fi

# 6. traefik/acme.json
if [ -f "$ROOT/traefik/acme.json" ]; then
  perms=$(stat -c %a "$ROOT/traefik/acme.json" 2>/dev/null || stat -f %A "$ROOT/traefik/acme.json" 2>/dev/null || echo "?")
  if [ "$perms" = "600" ]; then
    echo -e "${GREEN}[OK]${NC} traefik/acme.json existe (permisos 600)."
  else
    echo -e "${YELLOW}[AVISO]${NC} traefik/acme.json existe pero permisos deberían ser 600."
    echo "  → chmod 600 $ROOT/traefik/acme.json"
  fi
else
  echo -e "${RED}[FALTA]${NC} No existe traefik/acme.json."
  echo "  → touch $ROOT/traefik/acme.json && chmod 600 $ROOT/traefik/acme.json"
  MISSING=$((MISSING + 1))
fi

# 7. UFW / puertos 80, 443
if command -v ufw &>/dev/null; then
  if ufw status 2>/dev/null | grep -q "Status: active"; then
    echo -e "${GREEN}[OK]${NC} UFW activo."
    ufw status 2>/dev/null | grep -E "80|443" || echo -e "  ${YELLOW}Comprueba:${NC} sudo ufw allow 80/tcp && sudo ufw allow 443/tcp"
  else
    echo -e "${YELLOW}[AVISO]${NC} UFW instalado pero no activo."
    echo "  → sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable"
  fi
else
  echo -e "${YELLOW}[OPCIONAL]${NC} UFW no instalado (firewall)."
  echo "  → sudo apt install -y ufw && sudo ufw allow 22,80,443/tcp && sudo ufw enable"
fi

# 8. Contenedores (Traefik, portal)
echo ""
echo "--- Contenedores ---"
if command -v docker &>/dev/null; then
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "traefik"; then
    echo -e "${GREEN}[OK]${NC} Contenedor 'traefik' en ejecución."
  else
    echo -e "${RED}[FALTA]${NC} Traefik no está corriendo."
    echo "  → cd $ROOT && export \$(grep -v '^#' .env | xargs) && cd traefik && docker compose up -d && cd .."
    MISSING=$((MISSING + 1))
  fi
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "traefik"; then
    echo -e "${GREEN}[OK]${NC} Contenedor 'traefik' en ejecución."
  else
    echo -e "${RED}[FALTA]${NC} Traefik no está corriendo."
    echo "  → cd $ROOT/traefik && docker compose up -d"
    MISSING=$((MISSING + 1))
  fi
else
  echo "  (Docker no instalado; no se comprueban contenedores)"
fi

echo ""
if [ "$MISSING" -gt 0 ]; then
  echo -e "${RED}Resumen: $MISSING requisito(s) faltan.${NC} Sigue los comandos indicados arriba."
  echo "Para instalar todo de una vez: sudo ./setup-server.sh"
else
  echo -e "${GREEN}Todo listo.${NC} Si algo falla, revisa .env y reinicia: bash deploy.sh"
fi
