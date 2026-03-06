import os
import uuid

import httpx
import yt_dlp
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.download_dao import DownloadDAO

app = FastAPI(root_path="/instagram")
templates = Jinja2Templates(directory="app/templates")
_portal = (os.environ.get("PORTAL_URL") or "/").rstrip("/")
templates.env.globals["portal_url"] = _portal + "/" if _portal != "/" else "/"
templates.env.globals["favicon_url"] = _portal + "/static/favicon.png"

DOWNLOAD_DIR = "/app/data/downloads"
COOKIE_FILE = "/app/data/cookies.txt"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _get_ydl_base_opts():
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    if os.path.isfile(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE
    return opts


def _detect_media_type(url: str) -> str:
    if "/reel/" in url:
        return "Reel"
    if "/stories/" in url:
        return "Historia"
    return "Post"


def _best_thumbnail(info: dict) -> str | None:
    """Obtiene la mejor URL de thumbnail desde la info de yt-dlp (Instagram puede usar thumbnail o thumbnails)."""
    if info.get("thumbnail"):
        return info["thumbnail"]
    thumbnails = info.get("thumbnails") or []
    if not thumbnails:
        return None
    # Ordenar por preferencia o resolución (width) y quedarnos con la mejor
    def key(t):
        w = t.get("width") or t.get("preference") or 0
        return (w, t.get("id", 0))
    sorted_th = sorted(thumbnails, key=key, reverse=True)
    for t in sorted_th:
        url = t.get("url")
        if url:
            return url
    return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = DownloadDAO()
    history = dao.get_recent(limit=50)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "history": history, "user": user},
    )


@app.post("/preview")
async def preview(url: str = Form(...), user=Depends(verify_token)):
    """Detecta si es reel, historia o post y devuelve thumbnail (mejor disponible)."""
    if not url.strip():
        return JSONResponse({"error": "Escribe una URL de Instagram."}, status_code=400)
    if "instagram.com" not in url and "instagr.am" not in url:
        return JSONResponse({"error": "Solo se admiten enlaces de Instagram (instagram.com)."}, status_code=400)
    try:
        with yt_dlp.YoutubeDL(_get_ydl_base_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return JSONResponse({"error": "No se pudo obtener información del enlace. ¿Es público?"}, status_code=400)
            media_type = _detect_media_type(url)
            thumb = _best_thumbnail(info)
            return JSONResponse(
                {
                    "title": info.get("title"),
                    "thumbnail": thumb,
                    "type": media_type,
                    "uploader": info.get("uploader"),
                }
            )
    except yt_dlp.utils.DownloadError as e:
        msg = str(e).split("\n")[0] if str(e) else "Error al obtener la vista previa."
        if "Private" in str(e) or "login" in str(e).lower():
            msg = "El contenido es privado o requiere iniciar sesión. Prueba subiendo cookies.txt arriba."
        return JSONResponse({"error": msg}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)[:200]}"}, status_code=500)


@app.get("/thumbnail-proxy")
async def thumbnail_proxy(url: str = "", user=Depends(verify_token)):
    """Proxy del thumbnail para evitar CORS/referrer de Instagram."""
    if not url or not url.startswith(("http://", "https://")):
        return Response(status_code=400)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            r = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/119.0"},
            )
            r.raise_for_status()
            content_type = r.headers.get("content-type", "image/jpeg")
            return Response(content=r.content, media_type=content_type)
    except Exception:
        return Response(status_code=502)


@app.post("/download")
async def download(url: str = Form(...), user=Depends(verify_token)):
    filename = f"{uuid.uuid4()}.mp4"
    filepath = f"{DOWNLOAD_DIR}/{filename}"
    ydl_opts = {
        "outtmpl": filepath,
        "format": "bestvideo+bestaudio/best[ext=mp4]/best",
        "format_sort": ["res", "ext:mp4"],
        "merge_output_format": "mp4",
        "quiet": True,
        **_get_ydl_base_opts(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    file_size = 0
    if os.path.isfile(filepath):
        file_size = os.path.getsize(filepath)

    media_type = _detect_media_type(url)
    dao = DownloadDAO()
    dao.save(
        url=url,
        filename=filename,
        title=info.get("title"),
        uploader=info.get("uploader"),
        duration=info.get("duration"),
        file_size=file_size,
        media_type=media_type,
        username=user,
    )
    return FileResponse(
        filepath, filename=f"{info.get('title', 'video')}.mp4"
    )


@app.post("/upload-cookies")
async def upload_cookies(file: UploadFile = File(...), user=Depends(verify_token)):
    if not file.filename or not file.filename.lower().endswith(".txt"):
        return JSONResponse(
            {"error": "Sube un archivo .txt (cookies en formato Netscape)"},
            status_code=400,
        )
    path = COOKIE_FILE
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return JSONResponse({"ok": True, "message": "Cookies guardadas. Útil para historias privadas."})
