import io
import os
import zipfile

from PIL import Image
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token

app = FastAPI(root_path="/redimensionador")
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(_APP_DIR, "templates"))
_portal = (os.environ.get("PORTAL_URL") or "/").rstrip("/")
templates.env.globals["portal_url"] = _portal + "/" if _portal != "/" else "/"
templates.env.globals["favicon_url"] = _portal + "/static/favicon.png"

# Formatos por red y comunes. group sirve para agrupar en la UI.
PRESETS = [
    # TikTok
    {"id": "tiktok_video", "name": "Video / Story 9:16", "w": 1080, "h": 1920, "group": "tiktok"},
    {"id": "tiktok_square", "name": "Cuadrado (ad)", "w": 640, "h": 640, "group": "tiktok"},
    {"id": "tiktok_landscape", "name": "Horizontal (ad)", "w": 1920, "h": 1080, "group": "tiktok"},
    {"id": "tiktok_profile", "name": "Foto de perfil", "w": 200, "h": 200, "group": "tiktok"},
    # Instagram
    {"id": "ig_post", "name": "Post cuadrado", "w": 1080, "h": 1080, "group": "instagram"},
    {"id": "ig_post_45", "name": "Post 4:5 (recomendado feed)", "w": 1080, "h": 1350, "group": "instagram"},
    {"id": "ig_story", "name": "Story / Reel 9:16", "w": 1080, "h": 1920, "group": "instagram"},
    {"id": "ig_landscape", "name": "Horizontal", "w": 1080, "h": 566, "group": "instagram"},
    {"id": "ig_profile", "name": "Foto de perfil", "w": 320, "h": 320, "group": "instagram"},
    # YouTube
    {"id": "yt_thumb", "name": "Miniatura 16:9", "w": 1280, "h": 720, "group": "youtube"},
    {"id": "yt_shorts", "name": "Shorts 9:16", "w": 1080, "h": 1920, "group": "youtube"},
    {"id": "yt_banner", "name": "Banner canal", "w": 2560, "h": 1440, "group": "youtube"},
    {"id": "yt_profile", "name": "Foto de canal", "w": 800, "h": 800, "group": "youtube"},
    # Pinterest
    {"id": "pinterest_pin", "name": "Pin estándar 2:3", "w": 1000, "h": 1500, "group": "pinterest"},
    {"id": "pinterest_square", "name": "Pin cuadrado", "w": 1000, "h": 1000, "group": "pinterest"},
    {"id": "pinterest_long", "name": "Pin largo", "w": 1000, "h": 2100, "group": "pinterest"},
    {"id": "pinterest_story", "name": "Story 9:16", "w": 1080, "h": 1920, "group": "pinterest"},
    {"id": "pinterest_board", "name": "Portada de tablero", "w": 222, "h": 150, "group": "pinterest"},
    # Facebook
    {"id": "fb_post", "name": "Post enlace", "w": 1200, "h": 630, "group": "facebook"},
    {"id": "fb_story", "name": "Story 9:16", "w": 1080, "h": 1920, "group": "facebook"},
    {"id": "fb_square", "name": "Post cuadrado", "w": 1080, "h": 1080, "group": "facebook"},
    {"id": "fb_cover", "name": "Portada", "w": 820, "h": 312, "group": "facebook"},
    # Twitter / X
    {"id": "twitter_post", "name": "Post / imagen", "w": 1200, "h": 675, "group": "twitter"},
    {"id": "twitter_header", "name": "Cabecera", "w": 1500, "h": 500, "group": "twitter"},
    {"id": "twitter_card", "name": "Tarjeta resumen", "w": 1200, "h": 628, "group": "twitter"},
    # LinkedIn
    {"id": "linkedin_banner", "name": "Banner perfil", "w": 1584, "h": 396, "group": "linkedin"},
    {"id": "linkedin_post", "name": "Post", "w": 1200, "h": 627, "group": "linkedin"},
    {"id": "linkedin_bg", "name": "Fondo", "w": 1920, "h": 1080, "group": "linkedin"},
    {"id": "linkedin_logo", "name": "Logo empresa", "w": 300, "h": 300, "group": "linkedin"},
    # Formatos comunes
    {"id": "common_16_9", "name": "HD 16:9", "w": 1920, "h": 1080, "group": "comunes"},
    {"id": "common_9_16", "name": "Vertical 9:16", "w": 1080, "h": 1920, "group": "comunes"},
    {"id": "common_1_1", "name": "Cuadrado 1:1", "w": 1080, "h": 1080, "group": "comunes"},
    {"id": "common_4_5", "name": "4:5", "w": 1080, "h": 1350, "group": "comunes"},
    {"id": "common_2_3", "name": "2:3", "w": 1000, "h": 1500, "group": "comunes"},
    {"id": "common_a4", "name": "A4 (impresión)", "w": 2480, "h": 3508, "group": "comunes"},
]


def _resize_image(img: Image.Image, w: int, h: int) -> Image.Image:
    return img.copy().resize((w, h), Image.Resampling.LANCZOS)


def _presets_by_group():
    groups = {
        "tiktok": ("TikTok", []),
        "instagram": ("Instagram", []),
        "youtube": ("YouTube", []),
        "pinterest": ("Pinterest", []),
        "facebook": ("Facebook", []),
        "twitter": ("Twitter / X", []),
        "linkedin": ("LinkedIn", []),
        "comunes": ("Formatos comunes", []),
    }
    for p in PRESETS:
        g = p.get("group", "comunes")
        if g in groups:
            groups[g][1].append(p)
    return [(label, items) for label, items in groups.values() if items]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": user, "presets": PRESETS, "presets_by_group": _presets_by_group()},
    )


@app.post("/redimensionar")
async def redimensionar(
    request: Request,
    file: UploadFile = File(...),
    presets: str = Form("ig_post"),
    user=Depends(verify_token),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse({"error": "Sube una imagen (JPG, PNG, WebP)."}, status_code=400)
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        return JSONResponse({"error": "No se pudo leer la imagen."}, status_code=400)
    preset_ids = [s.strip() for s in (presets or "ig_post").split(",") if s.strip()]
    selected = [p for p in PRESETS if p["id"] in preset_ids]
    if not selected:
        selected = [PRESETS[0]]
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in selected:
                resized = _resize_image(img, p["w"], p["h"])
                f = io.BytesIO()
                resized.save(f, format="JPEG", quality=90)
                f.seek(0)
                zf.writestr(f"{p['id']}_{p['w']}x{p['h']}.jpg", f.getvalue())
        zip_bytes = buf.getvalue()
    except Exception:
        return JSONResponse({"error": "Error al generar el ZIP."}, status_code=500)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=redimensionadas.zip",
            "Content-Length": str(len(zip_bytes)),
        },
    )
