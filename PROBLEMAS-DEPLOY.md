# Problemas al hacer deploy en el servidor

Si los archivos ya están en el servidor pero el deploy falla, sigue esta guía.

---

## 1. Un solo comando: `deploy.sh`

En el servidor, desde la carpeta del proyecto:

```bash
cd ~/hidalgotech
bash deploy.sh
```

El script comprueba Docker, `.env`, SECRET_KEY, red y levanta Traefik + las apps. Si algo falla, muestra el error y qué hacer.

---

## 2. Comprobaciones antes de desplegar

### ¿Docker está instalado?

```bash
docker --version
docker compose version
```

Si no: `sudo bash setup-server.sh` (o instala Docker según DEPLOY.md).

### ¿Existe `.env` en la raíz del proyecto?

```bash
cd ~/hidalgotech
ls -la .env
```

Si no existe:

```bash
cp .env.example .env
nano .env
```

Rellena al menos:

- `SECRET_KEY=...` (genera con: `openssl rand -hex 32`)
- `DEFAULT_ADMIN_PASSWORD=...`
- `APP_ENV=production`

### ¿La red Docker `proxy` existe?

```bash
docker network ls | grep proxy
```

Si no: `docker network create proxy`

### ¿Existe `traefik/acme.json`?

```bash
touch ~/hidalgotech/traefik/acme.json
chmod 600 ~/hidalgotech/traefik/acme.json
```

---

## 3. Errores frecuentes

### `deploy.sh`: `$'\r': command not found` / `invalid option` / `syntax error`

El script tiene saltos de línea Windows (CRLF). En el servidor conviértelo a Linux (LF):

```bash
cd ~/hidalgotech
sed -i 's/\r$//' deploy.sh
sed -i 's/\r$//' setup-server.sh
sed -i 's/\r$//' check-server.sh
bash deploy.sh
```

Si subes de nuevo el proyecto (ZIP o git pull), el ZIP generado con `crear-zip-deploy.ps1` ya convierte los `.sh` a LF.

### Traefik: "client version 1.24 is too old. Minimum supported API version is 1.40"

El servidor tiene Docker reciente (API 1.40+) y la imagen Traefik v3.0 usa un cliente antiguo. Usa Traefik **v3.6** o superior (en el repo ya está `traefik:v3.6`). En el servidor:

```bash
cd ~/hidalgotech/traefik
# Edita docker-compose.yml y pon image: traefik:v3.6 (o sube el proyecto de nuevo)
docker compose pull
docker compose up -d --force-recreate
```

### Traefik: "unable to read directory /config: no such file or directory"

En `traefik.yml` estaba el provider `file` con `directory: /config` pero no se montaba. En el repo ya está quitado. En el servidor, edita `traefik/traefik.yml` y borra el bloque `file:` (las líneas de `file:` y `directory: /config` y `watch: true`). Luego: `cd ~/hidalgotech/traefik && docker compose up -d --force-recreate`.

### Apps: "unable to open database file" o contenedores en Restarting

Los contenedores corren como UID 1000 y no pueden escribir en sus carpetas `data`. En el servidor:

```bash
cd ~/hidalgotech
for dir in app-tiktok app-instagram app-margen app-moneda app-utm app-qr app-hashtags app-redimensionador app-roi app-pinterest app-transcriber app-costo-unidad; do
  mkdir -p "$dir/data"
  chown -R 1000:1000 "$dir/data"
done
export $(grep -v '^#' .env | xargs)
# Reiniciar apps que estaban en Restarting
for app in app-tiktok app-instagram app-margen app-moneda app-utm app-qr app-hashtags app-roi app-pinterest app-transcriber app-costo-unidad; do
  [ -f "$app/docker-compose.yml" ] && docker compose -f "$app/docker-compose.yml" up -d --build
done
```

### "SECRET_KEY no está definida" o las apps no arrancan

- Edita `.env` y pon una SECRET_KEY real (no la por defecto).
- Vuelve a ejecutar: `cd ~/hidalgotech && export $(grep -v '^#' .env | xargs) && bash deploy.sh`

### "network proxy not found"

```bash
docker network create proxy
```

### "permission denied" con Docker

Si no eres root:

```bash
sudo usermod -aG docker $USER
# Cierra sesión y vuelve a entrar por SSH
```

O ejecuta con sudo: `sudo bash deploy.sh`

### Traefik no arranca / puertos 80 o 443 en uso

```bash
sudo lsof -i :80
sudo lsof -i :443
```

Si otro proceso usa esos puertos, detén ese servicio o cambia la configuración.

### Contenedores que se reinician (crash loop)

```bash
docker ps -a
docker logs traefik
docker logs app-tiktok
```

Revisa los logs para ver el error (falta SECRET_KEY, falta .env, etc.).

### Dominio (hidalgotech.com) no resuelve

- Comprueba DNS: el dominio debe apuntar a la IP del servidor (registro A).
- Mientras tanto puedes probar por IP: `http://TU_IP/` (HTTPS puede dar error si el certificado es para el dominio).

### Los certificados SSL no se generan (HTTPS no funciona)

1. **acme.json** debe existir y tener permisos 600 (Traefik escribe aquí los certificados):
   ```bash
   touch ~/hidalgotech/traefik/acme.json
   chmod 600 ~/hidalgotech/traefik/acme.json
   ```
2. **Puerto 80** debe ser accesible desde internet para el reto HTTP-01 de Let's Encrypt. Comprueba que el firewall permite 80 y 443.
3. **Dominio**: el registro DNS (A) de `hidalgotech.com` debe apuntar a la IP del servidor.
4. Tras un cambio en Traefik, reinicia: `cd ~/hidalgotech/traefik && docker compose up -d --force-recreate`
5. Ver certificados generados: `cat ~/hidalgotech/traefik/acme.json | head -c 500`

### Entro admin y la contraseña pero no inicia sesión (redirige otra vez al login)

En producción (HTTPS) la cookie de sesión debe enviarse con `Secure`. Asegúrate de:

1. En el servidor, que el **portal** recibe las variables de entorno. En la raíz del proyecto, `.env` debe tener:
   ```bash
   DEFAULT_ADMIN_USER=admin
   DEFAULT_ADMIN_PASSWORD=050614
   SECRET_KEY=tu_clave_larga
   APP_ENV=production
   ```
2. Tras cambiar `.env`, reconstruir el portal:  
   `docker compose -f ~/hidalgotech/app-portal/docker-compose.yml up -d --build`
3. Probar en una ventana de incógnito para evitar cookies viejas.

---

## 4. Orden recomendado (a mano)

Si prefieres no usar `deploy.sh`:

```bash
cd ~/hidalgotech
export $(grep -v '^#' .env | xargs)
docker network create proxy 2>/dev/null || true
touch traefik/acme.json && chmod 600 traefik/acme.json
cd traefik && docker compose up -d && cd ..
docker compose -f portal/docker-compose.yml up -d --build
docker ps
```

---

## 5. Actualizar después de subir nuevos archivos

Si subes un nuevo ZIP o haces `git pull`:

```bash
cd ~/hidalgotech
export $(grep -v '^#' .env | xargs)
bash deploy.sh
```

---

Si el error que ves no está aquí, copia el mensaje exacto de la terminal (o el resultado de `docker logs traefik`) para poder afinar el diagnóstico.
