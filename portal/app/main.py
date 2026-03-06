import os
import time

import httpx
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from .auth import create_token, verify_password, verify_token, hash_password
from .dao.user_dao import UserDAO
from .security import generate_csrf_token, verify_csrf, rate_limit_check

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI()
IS_DEV = os.environ.get("APP_ENV") == "development"
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory=os.path.join(_APP_DIR, "static")), name="static")

# Ruta base del portal (ej. "" o "/portal") para cuando Traefik monta el portal en un subpath
# Se obtiene de PORTAL_URL: https://dominio.com/portal/ -> /portal
_portal_url = (os.environ.get("PORTAL_URL") or "").strip().rstrip("/")
PORTAL_PATH = ""
if _portal_url:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(_portal_url)
        path = (parsed.path or "").strip()
        if path and path != "/":
            PORTAL_PATH = path.rstrip("/")
    except Exception:
        pass
templates.env.globals["portal_path"] = PORTAL_PATH

def _url(path: str) -> str:
    """Prefija path con PORTAL_PATH para redirects y Location."""
    path = (path or "/").strip()
    if not path.startswith("/"):
        path = "/" + path
    return (PORTAL_PATH + path) if PORTAL_PATH else path

# Longitud mínima de contraseña (RNFS)
PASSWORD_MIN_LENGTH = 8


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limita peticiones por IP para mitigar abuso (no aplica a /static)."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/static/"):
            return await call_next(request)
        ip = _client_ip(request)
        if not rate_limit_check(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas peticiones. Intenta más tarde."},
                headers={"Retry-After": "300"},
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Cabeceras OWASP: clickjacking, MIME sniffing, CSP, HSTS, cache sensible."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # CSP: permitir CDN usados (Tailwind, Alpine, fuentes) y evitar XSS
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
        proto = (request.headers.get("x-forwarded-proto") or "").strip().lower()
        if proto == "https" and not IS_DEV:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # No cachear páginas sensibles ni API
        path = request.url.path
        if path.startswith(("/dashboard", "/admin", "/cuenta", "/api", "/ayuda")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)


async def get_current_user(request: Request, user=Depends(verify_token)):
    """Devuelve el objeto User desde la BD (con role)."""
    dao = UserDAO()
    u = dao.get_by_username(user)
    if not u:
        raise HTTPException(status_code=302, headers={"Location": _url("/")})
    return u


def require_admin(user=Depends(get_current_user)):
    """Solo permite acceso si el usuario tiene rol admin o es el usuario por defecto (por si la BD es antigua)."""
    if getattr(user, "role", None) == "admin":
        return user
    if getattr(user, "username", None) == DEFAULT_ADMIN_USER:
        return user
    raise HTTPException(status_code=403, detail="admin_required")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Para 403 'admin_required' devuelve una página HTML clara."""
    if exc.status_code == 403 and exc.detail == "admin_required":
        return templates.TemplateResponse(
            "403_admin.html",
            {"request": request},
            status_code=403,
        )
    if exc.status_code == 302:
        location = (exc.headers or {}).get("Location", _url("/"))
        return RedirectResponse(url=location, status_code=302)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# Cache para TRM y BTC (segundos)
_rates_cache = {"trm": None, "btc_usd": None, "ts": 0}
RATES_CACHE_TTL = 300  # 5 minutos

# Rate limiting login: máx intentos por IP
_login_attempts: dict[str, tuple[int, float]] = {}
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SEC = 900  # 15 minutos

# Usuario y contraseña por defecto (cámbialos en producción)
# .strip() previene problemas con \r de archivos .env con CRLF (Windows)
DEFAULT_ADMIN_USER = os.environ.get("DEFAULT_ADMIN_USER", "admin").strip()
DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123").strip()


@app.on_event("startup")
def ensure_default_admin():
    """Si no existe el usuario admin, lo crea con la contraseña por defecto y rol admin. Si existe, asegura que tenga rol admin."""
    dao = UserDAO()
    u = dao.get_by_username(DEFAULT_ADMIN_USER)
    if not u:
        dao.create_user(DEFAULT_ADMIN_USER, hash_password(DEFAULT_ADMIN_PASSWORD), role="admin")
        print("Usuario por defecto creado (cambia la contraseña en producción)")
    else:
        # Por si la BD es antigua o el rol quedó en operador, forzar admin para el usuario por defecto
        if getattr(u, "role", None) != "admin":
            dao.update_role(DEFAULT_ADMIN_USER, "admin")


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("login.html", {"request": request, "csrf_token": csrf_token})
    response.set_cookie("csrf_token", csrf_token, httponly=True, samesite="lax", path="/", max_age=3600)
    return response


def _client_ip(request: Request) -> str:
    """IP del cliente (respeta X-Forwarded-For detrás de proxy)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str | None = Form(None),
):
    if not verify_csrf(request.cookies.get("csrf_token"), csrf_token):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Sesión expirada o token inválido. Recarga la página e intenta de nuevo."},
            status_code=403,
        )
    ip = _client_ip(request)
    now = time.time()
    # Limpiar intentos antiguos
    if ip in _login_attempts:
        count, reset_at = _login_attempts[ip]
        if now > reset_at:
            del _login_attempts[ip]
        elif count >= LOGIN_MAX_ATTEMPTS:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Demasiados intentos. Espera 15 minutos e inténtalo de nuevo."},
            )
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario y contraseña son obligatorios."},
        )
    dao = UserDAO()
    user = dao.get_by_username(username)
    if not user:
        _login_attempts[ip] = (_login_attempts.get(ip, (0, now))[0] + 1, now + LOGIN_LOCKOUT_SEC)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales inválidas"},
        )
    if not getattr(user, "is_active", 1):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario desactivado. Contacta al administrador."},
        )
    if not verify_password(password, user.hashed_password):
        _login_attempts[ip] = (_login_attempts.get(ip, (0, now))[0] + 1, now + LOGIN_LOCKOUT_SEC)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales inválidas"},
        )
    if ip in _login_attempts:
        del _login_attempts[ip]
    token = create_token({"sub": username})
    response = RedirectResponse(_url("/dashboard"), status_code=302)
    # Secure=True solo si el cliente usó HTTPS (X-Forwarded-Proto detrás de Traefik); si no, la cookie no se envía y hay 302 en /dashboard
    proto = (request.headers.get("x-forwarded-proto") or "").strip().lower()
    secure_cookie = proto == "https" if proto else (not IS_DEV)
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
        max_age=8 * 3600,
    )
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user)):
    if IS_DEV:
        apps = [
            {"name": "TikTok Downloader", "url": "http://localhost:8001/", "icon": "🎵", "color": "from-pink-500 to-red-500"},
            {"name": "Instagram Downloader", "url": "http://localhost:8002/", "icon": "📸", "color": "from-purple-500 to-pink-500"},
            {"name": "Calculadora de margen", "url": "http://localhost:8003/", "icon": "📊", "color": "from-emerald-500 to-teal-500"},
            {"name": "Conversor de moneda", "url": "http://localhost:8004/", "icon": "💱", "color": "from-amber-500 to-yellow-600"},
            {"name": "UTM y Short links", "url": "http://localhost:8005/", "icon": "🔗", "color": "from-sky-500 to-blue-600"},
            {"name": "Generador QR", "url": "http://localhost:8006/", "icon": "📱", "color": "from-violet-500 to-purple-600"},
            {"name": "Hashtags y copy", "url": "http://localhost:8008/", "icon": "✍️", "color": "from-violet-500 to-purple-600"},
            {"name": "Redimensionador", "url": "http://localhost:8009/", "icon": "🖼️", "color": "from-cyan-500 to-blue-600"},
            {"name": "Calculadora ROI/ROAS", "url": "http://localhost:8010/", "icon": "📈", "color": "from-rose-500 to-red-500"},
            {"name": "Pinterest Downloader", "url": "http://localhost:8011/", "icon": "📌", "color": "from-red-600 to-red-700"},
            {"name": "YouTube Transcriber", "url": "http://localhost:8012/", "icon": "📝", "color": "from-amber-500 to-orange-600"},
        ]
    else:
        apps = [
            {"name": "TikTok Downloader", "url": "/tiktok/", "icon": "🎵", "color": "from-pink-500 to-red-500"},
            {"name": "Instagram Downloader", "url": "/instagram/", "icon": "📸", "color": "from-purple-500 to-pink-500"},
            {"name": "Calculadora de margen", "url": "/margen/", "icon": "📊", "color": "from-emerald-500 to-teal-500"},
            {"name": "Conversor de moneda", "url": "/moneda/", "icon": "💱", "color": "from-amber-500 to-yellow-600"},
            {"name": "UTM y Short links", "url": "/utm/", "icon": "🔗", "color": "from-sky-500 to-blue-600"},
            {"name": "Generador QR", "url": "/qr/", "icon": "📱", "color": "from-violet-500 to-purple-600"},
            {"name": "Hashtags y copy", "url": "/hashtags/", "icon": "✍️", "color": "from-violet-500 to-purple-600"},
            {"name": "Redimensionador", "url": "/redimensionador/", "icon": "🖼️", "color": "from-cyan-500 to-blue-600"},
            {"name": "Calculadora ROI/ROAS", "url": "/roi/", "icon": "📈", "color": "from-rose-500 to-red-500"},
            {"name": "Pinterest Downloader", "url": "/pinterest/", "icon": "📌", "color": "from-red-600 to-red-700"},
            {"name": "YouTube Transcriber", "url": "/transcriber/", "icon": "📝", "color": "from-amber-500 to-orange-600"},
        ]
    # Usuario por defecto siempre se considera admin para mostrar el panel (por si la BD es antigua)
    is_admin = getattr(user, "role", None) == "admin" or (getattr(user, "username", None) == DEFAULT_ADMIN_USER)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "apps": apps, "user": user, "is_admin": is_admin}
    )


@app.get("/logout")
async def logout():
    response = RedirectResponse(_url("/"), status_code=302)
    response.delete_cookie("access_token", path="/")
    return response


@app.get("/cuenta", response_class=HTMLResponse)
async def cuenta(
    request: Request,
    user=Depends(get_current_user),
    password_updated: str | None = None,
    password_error: str | None = None,
):
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse(
        "cuenta.html",
        {
            "request": request,
            "user": user,
            "is_admin": getattr(user, "role", None) == "admin",
            "password_updated": password_updated,
            "password_error": password_error,
            "csrf_token": csrf_token,
        },
    )
    response.set_cookie("csrf_token", csrf_token, httponly=True, samesite="lax", path="/", max_age=3600)
    return response


@app.post("/cuenta/password")
async def cuenta_change_password(
    request: Request,
    user=Depends(get_current_user),
    current_password: str = Form(...),
    new_password: str = Form(...),
    csrf_token: str | None = Form(None),
):
    """Cambiar contraseña del usuario actual. Redirige a /cuenta con mensaje."""
    if not verify_csrf(request.cookies.get("csrf_token"), csrf_token):
        return RedirectResponse(_url("/cuenta?password_error=csrf"), status_code=302)
    current_password = (current_password or "").strip()
    new_password = (new_password or "").strip()
    if not new_password:
        return RedirectResponse(_url("/cuenta?password_error=empty"), status_code=302)
    if len(new_password) < PASSWORD_MIN_LENGTH:
        return RedirectResponse(_url("/cuenta?password_error=length"), status_code=302)
    if not verify_password(current_password, user.hashed_password):
        return RedirectResponse(_url("/cuenta?password_error=current"), status_code=302)
    dao = UserDAO()
    dao.update_password(user.username, hash_password(new_password))
    return RedirectResponse(_url("/cuenta?password_updated=1"), status_code=302)


@app.get("/ayuda", response_class=HTMLResponse)
async def ayuda(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "ayuda.html",
        {"request": request, "user": user, "is_admin": getattr(user, "role", None) == "admin"},
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, user=Depends(require_admin)):
    dao = UserDAO()
    users = dao.list_users()
    password_reset = request.query_params.get("password_reset")
    password_reset_error = request.query_params.get("password_reset_error")
    deleted = request.query_params.get("deleted")
    delete_error = request.query_params.get("delete_error")
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "is_admin": True,
            "password_reset": password_reset,
            "password_reset_error": password_reset_error,
            "deleted": deleted,
            "delete_error": delete_error,
            "csrf_token": csrf_token,
        },
    )
    response.set_cookie("csrf_token", csrf_token, httponly=True, samesite="lax", path="/", max_age=3600)
    return response


@app.post("/admin/users")
async def admin_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("operador"),
    csrf_token: str | None = Form(None),
    admin=Depends(require_admin),
):
    if not verify_csrf(request.cookies.get("csrf_token"), csrf_token):
        raise HTTPException(status_code=403, detail="Token de seguridad inválido.")
    dao = UserDAO()
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "user": admin, "users": dao.list_users(), "error": "Usuario y contraseña son obligatorios.", "is_admin": True},
        )
    if dao.get_by_username(username):
        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "user": admin, "users": dao.list_users(), "error": "El usuario ya existe.", "is_admin": True},
        )
    if len(password) < PASSWORD_MIN_LENGTH:
        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "user": admin, "users": dao.list_users(), "error": f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.", "is_admin": True},
        )
    dao.create_user(username, hash_password(password), role=role if role in ("admin", "operador") else "operador")
    return RedirectResponse(_url("/admin"), status_code=302)


@app.post("/admin/users/{username}/role")
async def admin_update_role(
    request: Request,
    username: str,
    role: str = Form(...),
    csrf_token: str | None = Form(None),
    admin=Depends(require_admin),
):
    if not verify_csrf(request.cookies.get("csrf_token"), csrf_token):
        raise HTTPException(status_code=403, detail="Token de seguridad inválido.")
    dao = UserDAO()
    dao.update_role(username, role)
    return RedirectResponse(_url("/admin"), status_code=302)


@app.post("/admin/users/{username}/password")
async def admin_reset_password(
    request: Request,
    username: str,
    password: str = Form(..., alias="new_password"),
    csrf_token: str | None = Form(None),
    admin=Depends(require_admin),
):
    """Resetear contraseña de un usuario. Los datos se guardan en la BD (portal.db)."""
    if not verify_csrf(request.cookies.get("csrf_token"), csrf_token):
        return RedirectResponse(_url("/admin?password_reset_error=csrf"), status_code=302)
    password = (password or "").strip()
    if not password:
        return RedirectResponse(
            _url("/admin?password_reset_error=empty"),
            status_code=302,
        )
    if len(password) < PASSWORD_MIN_LENGTH:
        return RedirectResponse(
            _url("/admin?password_reset_error=length"),
            status_code=302,
        )
    dao = UserDAO()
    u = dao.get_by_username(username)
    if not u:
        return RedirectResponse(
            _url("/admin?password_reset_error=user"),
            status_code=302,
        )
    dao.update_password(username, hash_password(password))
    return RedirectResponse(
        _url(f"/admin?password_reset={username}"),
        status_code=302,
    )


@app.post("/admin/users/{username}/delete")
async def admin_delete_user(
    request: Request,
    username: str,
    csrf_token: str | None = Form(None),
    admin=Depends(require_admin),
):
    """Elimina un usuario. No se puede borrar el usuario admin por defecto si es el último admin."""
    if not verify_csrf(request.cookies.get("csrf_token"), csrf_token):
        raise HTTPException(status_code=403, detail="Token de seguridad inválido.")
    dao = UserDAO()
    users = dao.list_users()
    admins = [u for u in users if getattr(u, "role", None) == "admin"]
    if len(admins) <= 1 and getattr(dao.get_by_username(username), "role", None) == "admin":
        return RedirectResponse(
            _url("/admin?delete_error=last_admin"),
            status_code=302,
        )
    if dao.delete_user(username):
        return RedirectResponse(_url("/admin?deleted=" + username), status_code=302)
    return RedirectResponse(_url("/admin?delete_error=user"), status_code=302)


@app.get("/api/rates")
async def api_rates(user=Depends(verify_token)):
    """TRM USD/COP (Colombia) y BTC en USD. Cache 5 min."""
    global _rates_cache
    now = time.time()
    if _rates_cache["ts"] and (now - _rates_cache["ts"]) < RATES_CACHE_TTL:
        return JSONResponse({
            "trm": _rates_cache["trm"],
            "btc_usd": _rates_cache["btc_usd"],
        })
    trm, btc_usd = None, None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            # TRM Colombia (DolarApi)
            r = await client.get("https://co.dolarapi.com/v1/trm")
            if r.status_code == 200:
                data = r.json()
                trm = float(data.get("valor", 0) or 0)
            if trm is None:
                r2 = await client.get("https://api.frankfurter.app/latest?from=USD&to=COP")
                if r2.status_code == 200:
                    trm = float(r2.json().get("rates", {}).get("COP", 0))
            # BTC USD
            r3 = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
            if r3.status_code == 200:
                btc_usd = float(r3.json().get("bitcoin", {}).get("usd", 0) or 0)
    except Exception:
        pass
    _rates_cache["trm"] = trm
    _rates_cache["btc_usd"] = btc_usd
    _rates_cache["ts"] = now
    return JSONResponse({"trm": trm, "btc_usd": btc_usd})
