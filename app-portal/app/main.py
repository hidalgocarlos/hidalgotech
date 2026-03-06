import os
import secrets
from datetime import datetime, timedelta

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt

SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_THIS_TO_256_BIT_SECRET").strip()
ALGORITHM = "HS256"
ADMIN_USER = os.environ.get("DEFAULT_ADMIN_USER", "admin").strip()
ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "").strip()

APPS = [
    {"name": "TikTok Downloader", "path": "/tiktok", "desc": "Descarga videos sin marca de agua"},
    {"name": "Instagram Downloader", "path": "/instagram", "desc": "Reels, posts e historias"},
    {"name": "Pinterest Downloader", "path": "/pinterest", "desc": "Descarga imagenes y videos"},
    {"name": "Transcriptor", "path": "/transcriber", "desc": "Transcribe audio a texto con IA"},
    {"name": "Calculadora de margen", "path": "/margen", "desc": "Margen neto y % de beneficio"},
    {"name": "Conversor de moneda", "path": "/moneda", "desc": "Tipos de cambio en tiempo real"},
    {"name": "UTM Builder", "path": "/utm", "desc": "Genera y guarda parametros UTM"},
    {"name": "Generador QR", "path": "/qr", "desc": "Genera codigos QR personalizados"},
    {"name": "Generador de hashtags", "path": "/hashtags", "desc": "Hashtags con IA para redes sociales"},
    {"name": "Redimensionador", "path": "/redimensionador", "desc": "Redimensiona imagenes en lote"},
    {"name": "Calculadora ROI", "path": "/roi", "desc": "Calcula el retorno de inversion"},
    {"name": "Costo por unidad", "path": "/costo-unidad", "desc": "Calcula el costo unitario"},
]

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


def _create_token(username: str) -> str:
    exp = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode({"sub": username, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def _get_user(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = _get_user(request)
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user or "Visitante", "apps": APPS}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    redirect_uri = request.query_params.get("redirect_uri", "/")
    return templates.TemplateResponse("login.html", {"request": request, "redirect_uri": redirect_uri})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    redirect_uri = request.query_params.get("redirect_uri", "/")
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        token = _create_token(ADMIN_USER)
        response = RedirectResponse(url=redirect_uri, status_code=302)
        response.set_cookie(key="access_token", value=token, httponly=True, samesite="Lax")
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Usuario o contraseña incorrectos", "redirect_uri": redirect_uri})
