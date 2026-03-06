#!/bin/bash
# deploy.sh — Ejecutar EN EL SERVIDOR para levantar Traefik + portal + apps.
# Uso: cd ~/hidalgotech && bash deploy.sh
# Requisitos: Docker instalado, .env con SECRET_KEY y DEFAULT_ADMIN_PASSWORD

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "=== Deploy hidalgotech (desde $ROOT) ==="

# 1. Comprobar Docker
if ! command -v docker &>/dev/null; then
  echo "ERROR: Docker no está instalado. Ejecuta primero: sudo bash setup-server.sh"
  exit 1
fi
if ! docker compose version &>/dev/null; then
  echo "ERROR: Docker Compose no disponible. Instala: sudo apt install -y docker-compose-plugin"
  exit 1
fi

# 2. Comprobar .env
if [ ! -f "$ROOT/.env" ]; then
  echo "ERROR: No existe .env en la raíz del proyecto."
  echo "  Cópialo: cp $ROOT/.env.example $ROOT/.env"
  echo "  Edítalo: nano $ROOT/.env"
  echo "  Debe tener al menos: SECRET_KEY=..., DEFAULT_ADMIN_PASSWORD=..., PORTAL_URL=https://hidalgotech.com/"
  exit 1
fi

# 3. Cargar .env (exportar variables para docker compose)
# Nota: evita espacios o comillas raras en los valores de .env
export $(grep -v '^#' "$ROOT/.env" | grep -v '^$' | xargs)
if [ -z "${SECRET_KEY}" ] || [ "${SECRET_KEY}" = "CHANGE_THIS_TO_256_BIT_SECRET" ]; then
  echo "ERROR: SECRET_KEY no está definida o sigue por defecto en .env"
  echo "  Genera una: openssl rand -hex 32"
  echo "  Edita: nano $ROOT/.env"
  exit 1
fi

# 4. Red Docker
if ! docker network inspect proxy &>/dev/null; then
  echo "Creando red Docker 'proxy'..."
  docker network create proxy
fi

# 5. Traefik acme.json
mkdir -p "$ROOT/traefik"
touch "$ROOT/traefik/acme.json"
chmod 600 "$ROOT/traefik/acme.json"

# 5b. Permisos para data (contenedores corren como UID 1000)
mkdir -p "$ROOT/portal/data"
chown -R 1000:1000 "$ROOT/portal/data" 2>/dev/null || true
for dir in app-tiktok app-instagram app-margen app-moneda app-utm app-qr app-hashtags app-redimensionador app-roi app-pinterest app-transcriber app-costo-unidad; do
  [ -d "$ROOT/$dir" ] && mkdir -p "$ROOT/$dir/data" && chown -R 1000:1000 "$ROOT/$dir/data" 2>/dev/null || true
done

# 6. Levantar Traefik
echo "Levantando Traefik..."
cd "$ROOT/traefik"
docker compose up -d
cd "$ROOT"

# 7. Levantar portal
echo "Levantando portal..."
docker compose -f portal/docker-compose.yml up -d --build
echo "Portal en marcha (puertos 80/443 vía Traefik)."

# 8. Apps opcionales (descomenta si las usas)
APPS="app-tiktok app-instagram app-margen app-moneda app-utm app-qr app-hashtags app-redimensionador app-roi app-pinterest app-transcriber app-costo-unidad"
for app in $APPS; do
  if [ -f "$ROOT/$app/docker-compose.yml" ]; then
    echo "Levantando $app..."
    docker compose -f "$ROOT/$app/docker-compose.yml" up -d --build
  fi
done

echo ""
echo "=== Deploy terminado ==="
echo "Comprueba: docker ps"
echo "Si usas dominio: https://hidalgotech.com/"
echo "Si solo IP: http://TU_IP/ (HTTPS puede fallar sin dominio)"
