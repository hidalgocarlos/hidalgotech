# Plantilla App Nueva

Para agregar una nueva app al AppHub:

1. Copia la carpeta `app-nueva/` y renómbrala (ej. `app-youtube/`).
2. En `docker-compose.yml`: cambia `PathPrefix(/nueva)` por tu ruta (ej. `/youtube`), y los nombres de router/middleware/service (ej. `youtube`).
3. En `app/main.py`: cambia `root_path="/nueva"` por tu path (ej. `root_path="/youtube"`).
4. Si necesitas auth: copia `auth.py` desde `portal/app/auth.py` y usa `Depends(verify_token)` en las rutas.
5. Si necesitas DB: crea `models/` y `dao/` como en app-tiktok, y usa SQLite en `/app/data/nombre.db`.
6. Añade la app al menú del portal en `portal/app/main.py` (lista `apps` en `dashboard`).
7. Ejecuta `docker compose up -d` en la carpeta de la app. Traefik la detectará automáticamente.
