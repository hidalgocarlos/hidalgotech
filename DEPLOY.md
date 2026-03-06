# Despliegue en hidalgotech.com

Guía para subir el código con Git y desplegar en el servidor con SSL (Let's Encrypt) y seguridad estricta.

---

## 1. Git: preparar y subir el código

### En tu máquina local (Windows PowerShell)

```powershell
cd c:\Users\hidal\Downloads\hidalgotech

# Inicializar repositorio (si aún no existe)
git init

# Añadir todos los archivos (respeta .gitignore)
git add .
git status

# Primer commit
git commit -m "ToolBox Pro: portal + apps, seguridad y SSL listos para producción"

# Añadir el remoto (elige una opción)
# Opción A: GitHub
git remote add origin https://github.com/TU_USUARIO/hidalgotech.git

# Opción B: GitLab
# git remote add origin https://gitlab.com/TU_USUARIO/hidalgotech.git

# Opción C: Servidor vía SSH (reemplaza usuario e IP/dominio)
# git remote add origin ssh://usuario@hidalgotech.com/home/usuario/hidalgotech.git

# Subir (primera vez)
git branch -M main
git push -u origin main
```

### Siguientes actualizaciones (local)

```powershell
cd c:\Users\hidal\Downloads\hidalgotech
git add .
git commit -m "Descripción del cambio"
git push origin main
```

---

## 2. En el servidor (Linux con Docker)

### Requisitos

- Docker y Docker Compose instalados
- Dominio `hidalgotech.com` apuntando a la IP del servidor (registro DNS tipo A)
- Puertos 80 y 443 abiertos en el firewall

### Primera vez: clonar y configurar

```bash
# Clonar (o si ya tienes la carpeta, solo pull)
cd /home/tu_usuario   # o la ruta que uses
git clone https://github.com/TU_USUARIO/hidalgotech.git
cd hidalgotech
# O si ya existe el repo:
# cd hidalgotech && git pull origin main
```

### Crear red Docker para Traefik

```bash
docker network create proxy
```

### Certificados SSL (Let's Encrypt)

Traefik ya está configurado para obtener certificados automáticamente. Solo hay que crear el archivo y dar permisos:

```bash
touch traefik/acme.json
chmod 600 traefik/acme.json
```

### Variables de entorno (seguridad)

Crear un archivo `.env` en la raíz del proyecto (no se sube a git):

```bash
# .env en la raíz (para el portal y apps)
# Genera una clave segura: openssl rand -hex 32
SECRET_KEY=tu_clave_secreta_de_al_menos_32_caracteres_aleatoria
APP_ENV=production
PORTAL_URL=https://hidalgotech.com/
DEFAULT_ADMIN_USER=admin
DEFAULT_ADMIN_PASSWORD=CambiaEstoPorUnaContraseñaSegura123!
```

Para generar una SECRET_KEY segura:

```bash
openssl rand -hex 32
```

### Levantar Traefik primero

```bash
cd traefik
docker compose up -d
cd ..
```

### Levantar el portal y las apps

Cada servicio tiene su propio `docker-compose.yml` con labels de Traefik. Hay que levantar cada uno en el mismo host y con la red `proxy`. Opciones:

**Opción A – Script para levantar todos (crear `deploy.sh`):**

```bash
#!/bin/bash
set -e
export $(grep -v '^#' .env | xargs)

docker compose -f portal/docker-compose.yml up -d --build
docker compose -f app-tiktok/docker-compose.yml up -d --build
docker compose -f app-instagram/docker-compose.yml up -d --build
docker compose -f app-margen/docker-compose.yml up -d --build
docker compose -f app-moneda/docker-compose.yml up -d --build
docker compose -f app-utm/docker-compose.yml up -d --build
docker compose -f app-qr/docker-compose.yml up -d --build
docker compose -f app-hashtags/docker-compose.yml up -d --build
docker compose -f app-redimensionador/docker-compose.yml up -d --build
docker compose -f app-roi/docker-compose.yml up -d --build
docker compose -f app-pinterest/docker-compose.yml up -d --build
docker compose -f app-transcriber/docker-compose.yml up -d --build
```

El `portal/docker-compose.yml` ya incluye las variables de entorno. **Importante:** todas las apps (tiktok, instagram, etc.) deben recibir la misma `SECRET_KEY` para validar el JWT del portal. Añade en cada `app-*/docker-compose.yml` de producción:

```yaml
environment:
  - SECRET_KEY=${SECRET_KEY}
  - PORTAL_URL=${PORTAL_URL}
  - APP_ENV=production
```

**Opción B – Comandos manuales (con .env cargado):**

```bash
export $(grep -v '^#' .env | xargs)
cd portal && docker compose up -d --build && cd ..
cd app-tiktok && docker compose up -d --build && cd ..
# ... repetir para cada app
```

### Actualizar después de un `git pull`

```bash
cd /home/tu_usuario/hidalgotech
git pull origin main
export $(grep -v '^#' .env | xargs)
# Reconstruir y levantar solo lo que cambió, por ejemplo:
docker compose -f portal/docker-compose.yml up -d --build
```

---

## 3. SSL (certificados)

- **HTTP → HTTPS:** Traefik redirige todo el tráfico de `:80` a `:443` (configurado en `traefik/traefik.yml`).
- **Let's Encrypt:** Cada router tiene `tls.certresolver=letsencrypt`. Traefik pide y renueva los certificados automáticamente.
- **Dominio:** Los `docker-compose.yml` de producción usan `Host(\`hidalgotech.com\`)`. El primer acceso a https://hidalgotech.com puede tardar unos segundos mientras se obtiene el certificado.

Comprobar que el certificado se generó:

```bash
cat traefik/acme.json | jq '.letsencrypt.Certificates'
```

---

## 4. Seguridad aplicada

| Medida | Estado |
|--------|--------|
| **Contraseñas** | Solo se guardan hasheadas (bcrypt) en la BD. Nunca en plano. |
| **Cookie de sesión** | `httponly=True`, `secure=True` en producción, `samesite=lax`, `path=/`, `max_age=8h`. |
| **SECRET_KEY** | En producción debe venir de variable de entorno; si no, la app no arranca. |
| **Login** | Rate limiting: 5 intentos fallidos por IP → bloqueo 15 min. |
| **HTTPS** | Todo el tráfico pasa por Traefik con TLS (Let's Encrypt). |
| **Datos en tránsito** | Cifrados por HTTPS. |

### Comprobar en producción

1. **SECRET_KEY:** En el servidor, `echo $SECRET_KEY` no debe estar vacío y no debe ser el valor por defecto.
2. **HTTPS:** Abrir https://hidalgotech.com y comprobar el candado en el navegador.
3. **Cookie:** En DevTools → Application → Cookies, la cookie `access_token` debe tener HttpOnly y Secure.

---

## 5. Resumen de comandos

**Local (subir cambios):**
```powershell
git add .
git commit -m "mensaje"
git push origin main
```

**Servidor (recibir cambios y desplegar):**
```bash
cd /ruta/hidalgotech
git pull origin main
export $(grep -v '^#' .env | xargs)
# Reconstruir y levantar los servicios que hayas tocado, por ejemplo:
docker compose -f portal/docker-compose.yml up -d --build
```

**Servidor (primera vez – SSL):**
```bash
touch traefik/acme.json && chmod 600 traefik/acme.json
docker network create proxy
# Crear .env con SECRET_KEY, etc.
# Levantar Traefik y luego portal + apps
```
