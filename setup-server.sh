#!/bin/bash
# setup-server.sh — Prepara el servidor Ubuntu/Debian para hidalgotech
# Uso: 
#   Opción A: Desde tu PC, copia al servidor y ejecuta con la URL del repo:
#     scp setup-server.sh usuario@IP:/tmp/ && ssh usuario@IP "sudo bash /tmp/setup-server.sh https://github.com/hidalgocarlos/hidalgotech.git"
#   Opción B: En el servidor, después de clonar: chmod +x setup-server.sh && sudo ./setup-server.sh

set -e
GIT_REPO="${1:-}"
INSTALL_DIR="${HOME}/hidalgotech"

echo "=== Preparando servidor para hidalgotech ==="

# Necesitamos root para instalar paquetes
if [ "$(id -u)" -ne 0 ]; then
  echo "Ejecutando con sudo..."
  exec sudo bash "$0" "$@"
fi

# 1. Actualizar sistema
echo "[1/8] Actualizando sistema..."
apt-get update -qq && apt-get upgrade -y -qq

# 2. Instalar Git si no está (para clonar)
if ! command -v git &>/dev/null; then
  echo "[2/8] Instalando Git..."
  apt-get install -y -qq git
else
  echo "[2/8] Git ya instalado."
fi

# 3. Si no estamos en un repo git, clonar
if [ ! -d ".git" ]; then
  if [ -z "$GIT_REPO" ]; then
    echo "No estás dentro del repositorio y no se pasó URL."
    echo "Uso: sudo ./setup-server.sh https://github.com/hidalgocarlos/hidalgotech.git"
    exit 1
  fi
  echo "[3/8] Clonando repositorio en $INSTALL_DIR ..."
  sudo -u "${SUDO_USER:-root}" git clone "$GIT_REPO" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
else
  echo "[3/8] Ya estás en el repositorio."
  INSTALL_DIR="$(pwd)"
fi

# 4. Instalar Docker
if ! command -v docker &>/dev/null; then
  echo "[4/8] Instalando Docker..."
  apt-get install -y -qq ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release 2>/dev/null && echo "${VERSION_CODENAME}" || echo "jammy") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
  echo "[4/8] Docker ya instalado."
fi

# 5. Usuario al grupo docker
if [ -n "${SUDO_USER}" ] && [ "${SUDO_USER}" != "root" ]; then
  echo "[5/8] Añadiendo $SUDO_USER al grupo docker..."
  usermod -aG docker "${SUDO_USER}" 2>/dev/null || true
else
  echo "[5/8] Ejecutando como root; recuerda añadir tu usuario: usermod -aG docker tu_usuario"
fi

# 6. Firewall (22, 80, 443)
echo "[6/8] Configurando firewall (UFW)..."
apt-get install -y -qq ufw 2>/dev/null || true
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable 2>/dev/null || true
ufw status | head -5

# 7. Red Docker y certificados Traefik
echo "[7/8] Creando red Docker y archivo de certificados..."
docker network create proxy 2>/dev/null || true
mkdir -p "$INSTALL_DIR/traefik"
touch "$INSTALL_DIR/traefik/acme.json"
chmod 600 "$INSTALL_DIR/traefik/acme.json"

# 8. .env desde ejemplo si no existe
echo "[8/8] Configurando .env..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
  cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
  chown "${SUDO_USER:-root}:${SUDO_USER:-root}" "$INSTALL_DIR/.env" 2>/dev/null || true
  echo "  → Creado .env desde .env.example. Edítalo y pon SECRET_KEY y contraseña:"
  echo "     nano $INSTALL_DIR/.env"
else
  echo "  → .env ya existe."
fi

echo ""
echo "=== Servidor listo ==="
echo "1. Genera una SECRET_KEY:  openssl rand -hex 32"
echo "2. Edita .env:             nano $INSTALL_DIR/.env"
echo "3. Carga variables:        cd $INSTALL_DIR && export \$(grep -v '^#' .env | xargs)"
echo "4. Levanta Traefik:        cd $INSTALL_DIR/traefik && docker compose up -d && cd .."
echo "5. Levanta portal y apps:  docker compose -f portal/docker-compose.yml up -d --build"
echo "   (y el resto de apps según DEPLOY.md)"
echo ""
echo "Si añadiste tu usuario al grupo docker, cierra sesión y vuelve a entrar (o ejecuta: newgrp docker)."
