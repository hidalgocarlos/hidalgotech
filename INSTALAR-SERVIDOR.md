# Instalación del servidor desde cero (Ubuntu/Debian)

Conéctate por SSH como **root** (o usuario con sudo) y ejecuta estos bloques en orden.

---

## 1. Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 2. Instalar Docker

```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release 2>/dev/null && echo "${VERSION_CODENAME}" || echo "jammy") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

## 3. Comprobar Docker

```bash
docker --version
docker compose version
```

Deben salir versiones sin error.

---

## 4. (Opcional) Si no eres root: añadir tu usuario a docker

```bash
sudo usermod -aG docker $USER
```

Cierra sesión y vuelve a entrar por SSH para que tenga efecto (o ejecuta `newgrp docker`).

---

## 5. Firewall (puertos 22, 80, 443)

```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

---

## 6. Red Docker para Traefik

```bash
docker network create proxy
```

(Si dice "already exists", está bien.)

---

## 7. Tener el proyecto en el servidor

**Opción A — Ya subiste el ZIP (MobaXterm, etc.):**

- Descomprimir en tu home, por ejemplo:
  ```bash
  cd ~
  apt install -y unzip
  unzip -o hidalgotech-deploy.zip -d hidalgotech
  cd ~/hidalgotech
  ```

**Opción B — Clonar con Git:**

```bash
sudo apt install -y git
cd ~
git clone https://github.com/hidalgocarlos/hidalgotech.git
cd hidalgotech
```

---

## 8. Certificados SSL (Traefik) y .env

```bash
cd ~/hidalgotech
mkdir -p traefik
touch traefik/acme.json
chmod 600 traefik/acme.json
cp .env.example .env
nano .env
```

En `.env` pon al menos:

- `SECRET_KEY=...` (genera con: `openssl rand -hex 32`)
- `DEFAULT_ADMIN_PASSWORD=...`
- `APP_ENV=production`

Guarda (Ctrl+O, Enter, Ctrl+X).

---

## 9. Arrancar el sitio (deploy)

```bash
cd ~/hidalgotech
sed -i 's/\r$//' deploy.sh
bash deploy.sh
```

Si `deploy.sh` da error de `\r`, ejecuta antes:

```bash
sed -i 's/\r$//' deploy.sh setup-server.sh check-server.sh 2>/dev/null
```

---

## 10. Comprobar

```bash
docker ps
```

Deberías ver **traefik** y **portal**. Abre en el navegador:

- Con dominio: **https://hidalgotech.com/**
- Solo IP: **http://TU_IP/**

---

## Resumen rápido (orden)

| Paso | Qué hace |
|------|----------|
| 1 | `apt update && apt upgrade -y` |
| 2 | Instalar Docker (+ Compose plugin) |
| 3 | `docker --version` y `docker compose version` |
| 4 | (Opcional) `usermod -aG docker $USER` y reconectar SSH |
| 5 | UFW: allow 22, 80, 443 y enable |
| 6 | `docker network create proxy` |
| 7 | Proyecto en `~/hidalgotech` (ZIP o git clone) |
| 8 | `traefik/acme.json`, `.env` desde `.env.example`, editar `.env` |
| 9 | `sed -i 's/\r$//' deploy.sh && bash deploy.sh` |
| 10 | `docker ps` y abrir https://hidalgotech.com o http://IP |
