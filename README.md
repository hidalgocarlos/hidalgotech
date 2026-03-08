# Plataforma Docker Apps (AppHub)

Dominio: **hidalgotech.com**. Arquitectura de microservicios con Traefik como reverse proxy, Portal de login con JWT, y apps de descarga (TikTok, Instagram) usando yt-dlp. Cada app corre en su propio contenedor Docker con FastAPI + SQLite + SQLAlchemy. Pensado para despliegue en servidores Hetzner.

## Requisitos

- Docker y Docker Compose
- Dominio (hidalgotech.com) apuntando al servidor para SSL con Let's Encrypt (solo producción)

---

## Probar en local (mientras subes a Hetzner)

Se usa **un puerto por app** (sin Traefik), para evitar problemas con el socket de Docker en Windows.

1. **Arrancar todo** (desde la raíz del proyecto):

   ```powershell
   .\run-local.ps1
   ```

   O manualmente:

   ```bash
   docker compose -f docker-compose.local.yml up -d --build
   ```

2. **Acceso al portal** — Si es la primera vez, se crea un usuario por defecto:
   - **Usuario:** `admin`
   - **Contraseña:** `admin123`  
   (En producción cambia la contraseña o define `DEFAULT_ADMIN_PASSWORD` al levantar el portal.)

3. **Abrir en el navegador:**
   - **http://localhost:8000** — Portal (login)
   - **http://localhost:8001** — TikTok Downloader
   - **http://localhost:8002** — Instagram Downloader
   - **http://localhost:8003** — Calculadora de margen
   - **http://localhost:8004** — Conversor de moneda
   - **http://localhost:8005** — UTM y Short links
   - **http://localhost:8006** — Generador QR
   - **http://localhost:8007** — Costo por unidad
   - **http://localhost:8008** — Hashtags y copy
   - **http://localhost:8009** — Redimensionador de imágenes
   - **http://localhost:8010** — Calculadora ROI/ROAS
   - **http://localhost:8011** — Pinterest Downloader

El dashboard del portal (tras iniciar sesión) enlaza a todas las apps en modo desarrollo. En producción (Hetzner) se usa Traefik y rutas `/tiktok/`, `/instagram/`, `/margen/`, `/moneda/`, `/utm/`, `/qr/`, `/costo-unidad/`, `/hashtags/`, `/redimensionador/`, `/roi/`, `/pinterest/`.

---

## Despliegue completo (Hetzner / producción)

### 1. Crear la red proxy (una sola vez)

```bash
docker network create proxy
```

### 2. Levantar Traefik

```bash
cd traefik
touch acme.json && chmod 600 acme.json
docker compose up -d
```

El email para Let's Encrypt está en `traefik/traefik.yml` (admin@hidalgotech.com). Todas las apps usan el host `hidalgotech.com` en sus labels.

### 3. Levantar el Portal y las apps

```bash
cd portal && docker compose up -d
cd ../app-tiktok && docker compose up -d
cd ../app-instagram && docker compose up -d
cd ../app-margen && docker compose up -d
cd ../app-moneda && docker compose up -d
cd ../app-utm && docker compose up -d
cd ../app-qr && docker compose up -d
cd ../app-costo-unidad && docker compose up -d
cd ../app-hashtags && docker compose up -d
cd ../app-redimensionador && docker compose up -d
cd ../app-roi && docker compose up -d
cd ../app-pinterest && docker compose up -d
```

### 4. Usuario admin

Si no hay ningún usuario en la base de datos, el portal crea uno al arrancar:
- **Usuario:** `admin`
- **Contraseña:** `admin123`

Para cambiar la contraseña o crear otro usuario:  
`docker exec portal python setup_admin.py admin NuevaClave --reset`

### 5. Acceso

- **Portal (login y menú):** https://hidalgotech.com/
- **TikTok Downloader:** https://hidalgotech.com/tiktok/
- **Instagram Downloader:** https://hidalgotech.com/instagram/
- **Calculadora de margen:** https://hidalgotech.com/margen/
- **Conversor de moneda:** https://hidalgotech.com/moneda/
- **UTM y Short links:** https://hidalgotech.com/utm/
- **Generador QR:** https://hidalgotech.com/qr/
- **Costo por unidad:** https://hidalgotech.com/costo-unidad/
- **Hashtags y copy:** https://hidalgotech.com/hashtags/
- **Redimensionador:** https://hidalgotech.com/redimensionador/
- **Calculadora ROI/ROAS:** https://hidalgotech.com/roi/
- **Pinterest Downloader:** https://hidalgotech.com/pinterest/

## Estructura del proyecto

```
traefik/           # Reverse proxy + SSL Let's Encrypt
portal/            # Login + dashboard (menú de apps)
app-tiktok/        # Descargador TikTok (yt-dlp)
app-instagram/     # Descargador Instagram Reels/Stories/Posts + subida cookies.txt
app-margen/        # Calculadora de margen (coste + fee + impuesto → precio/margen)
app-moneda/        # Conversor de moneda (tipo manual, historial)
app-utm/           # UTM builder + short links (slug → redirect)
app-qr/            # Generador de códigos QR
app-costo-unidad/  # Calculadora costo por unidad (lote ÷ unidades)
app-hashtags/      # Generador de copy y hashtags por red
app-redimensionador/ # Redimensionar imágenes a tamaños por red social (ZIP)
app-roi/           # Calculadora ROI y ROAS publicitario
app-pinterest/     # Descargador Pinterest (pins imagen/video, yt-dlp)
_template-app/     # Plantilla para crear nuevas apps
```

## Agregar una nueva app

1. Copia la carpeta `_template-app/` y renómbrala (ej. `app-youtube/`).
2. En `docker-compose.yml`: cambia `template` por el nombre de tu app en router, middleware, service y `PathPrefix` (ej. `/youtube`).
3. En `app/main.py`: cambia `root_path="/template"` por `root_path="/youtube"`.
4. Ejecuta `docker compose up -d` en la carpeta de la nueva app. Traefik la detecta automáticamente.

## Notas

- **SSL**: Let's Encrypt gestiona los certificados vía Traefik en producción. En local se usa `docker-compose.local.yml` y `APP_ENV=development` para que la cookie funcione por HTTP.
- **Instagram cookies**: Para historias privadas, usa el formulario "Subir cookies" en la app Instagram o coloca un archivo `cookies.txt` (formato Netscape) en `app-instagram/data/`. La ruta usada por la app es `/app/data/cookies.txt`.
- **JWT**: Todas las apps comparten el mismo `SECRET_KEY` en `auth.py` para validar la cookie del portal. En producción, conviene usar una variable de entorno y el mismo valor en cada contenedor.
- **Hetzner**: Despliegue estándar; asegúrate de abrir los puertos 80 y 443 en el firewall y de que el DNS del dominio apunte a la IP del servidor.
