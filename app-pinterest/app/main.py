import os
import re
import uuid

import httpx
import yt_dlp
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.download_dao import DownloadDAO

app = FastAPI(root_path="/pinterest")
templates = Jinja2Templates(directory="app/templates")
_portal = (os.environ.get("PORTAL_URL") or "/").rstrip("/")
templates.env.globals["portal_url"] = _portal + "/" if _portal != "/" else "/"
templates.env.globals["favicon_url"] = _portal + "/static/favicon.png"

DOWNLOAD_DIR = "/app/data/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
YDL_OPTS_BASE = {
    "quiet": True,
    "no_warnings": True,
    "user_agent": USER_AGENT,
}

# Extensiones por Content-Type para fallback imagen
_CONTENT_TYPE_EXT = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


def _is_pinterest_url(url: str) -> bool:
    return "pinterest" in url or "pin.it" in url


async def _download_pin_image_fallback(pin_url: str, filepath: str) -> tuple[str, str, str] | None:
    """
    Cuando yt-dlp falla con «No video formats», intenta obtener la imagen del pin
    desde la página (og:image) y guardarla en filepath.<ext>. Devuelve (path, ext, title) o None.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(pin_url)
            r.raise_for_status()
            html = r.text
        # og:image: <meta property="og:image" content="https://...">
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not m:
            m = re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
        image_url = m.group(1).strip() if m else None
        if not image_url or not image_url.startswith("http"):
            return None
        title = "pin"
        tm = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if tm:
            title = tm.group(1).strip() or title
        else:
            tm = re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', html, re.I)
            if tm:
                title = tm.group(1).strip() or title
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers={"User-Agent": USER_AGENT}) as img_client:
            img = await img_client.get(image_url)
        img.raise_for_status()
        ct = (img.headers.get("content-type") or "").split(";")[0].strip().lower()
        ext = _CONTENT_TYPE_EXT.get(ct) or "jpg"
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            ext = "jpg"
        path = filepath + "." + ext
        with open(path, "wb") as f:
            f.write(img.content)
        return (path, ext, title)
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = DownloadDAO()
    history = dao.get_recent(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "history": history, "user": user})


@app.post("/preview")
async def preview(url: str = Form(...), user=Depends(verify_token)):
    url = (url or "").strip()
    if not url:
        return JSONResponse({"error": "Escribe una URL de Pinterest."}, status_code=400)
    if not _is_pinterest_url(url):
        return JSONResponse({"error": "Solo se admiten enlaces de Pinterest (pinterest.com o pin.it)."}, status_code=400)
    opts = {**YDL_OPTS_BASE, "format": "best"}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return JSONResponse({"error": "No se pudo obtener el pin. Comprueba que el enlace sea correcto y público."}, status_code=400)
        thumb = info.get("thumbnail") or (info.get("thumbnails") or [{}])[-1].get("url") if info.get("thumbnails") else None
        w, h = info.get("width"), info.get("height")
        res = f"{w}x{h}" if w and h else ""
        return JSONResponse({
            "title": info.get("title"),
            "thumbnail": thumb,
            "duration": info.get("duration"),
            "uploader": info.get("uploader") or info.get("creator"),
            "resolution": res,
        })
    except yt_dlp.utils.DownloadError as e:
        msg = str(e).split("\n")[0] if str(e) else "Error al analizar el pin."
        if "No video formats" in msg or "No video format" in msg:
            # Preview fallback: obtener og:image y og:title de la página
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=10.0, headers={"User-Agent": USER_AGENT}) as client:
                    r = await client.get(url)
                    r.raise_for_status()
                    html = r.text
                m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I) or re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
                thumb = m.group(1).strip() if m and m.group(1).startswith("http") else None
                t = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I) or re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', html, re.I)
                title = t.group(1).strip() if t else None
                if thumb:
                    return JSONResponse({"title": title, "thumbnail": thumb, "duration": None, "uploader": None, "resolution": ""})
            except Exception:
                pass
        return JSONResponse({"error": msg}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)[:200]}"}, status_code=500)


@app.post("/download")
async def download(url: str = Form(...), user=Depends(verify_token)):
    url = (url or "").strip()
    if not url or not _is_pinterest_url(url):
        return JSONResponse({"error": "URL de Pinterest no válida."}, status_code=400)
    filename = f"{uuid.uuid4()}"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    # Pins pueden ser solo imagen: usar "best" para aceptar video o imagen
    ydl_opts = {
        **YDL_OPTS_BASE,
        "outtmpl": filepath + ".%(ext)s",
        "format": "best",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        if not info:
            return JSONResponse({"error": "No se pudo obtener el contenido."}, status_code=400)
        ext = (info.get("ext") or "mp4").lower()
        if ext not in ("mp4", "webm", "mkv", "m4a", "jpg", "jpeg", "png", "webp", "gif"):
            ext = "mp4"
        actual_path = filepath + "." + ext
        if not os.path.isfile(actual_path):
            for e in ("mp4", "webm", "mkv", "m4a", "jpg", "jpeg", "png", "webp", "gif"):
                if os.path.isfile(filepath + "." + e):
                    actual_path = filepath + "." + e
                    ext = e
                    break
        if not os.path.isfile(actual_path):
            return JSONResponse({"error": "La descarga no generó ningún archivo. Prueba otro enlace."}, status_code=500)
        file_size = os.path.getsize(actual_path)
        safe_title = (info.get("title") or "pin").replace("/", "-").strip() or "pin"
        dao = DownloadDAO()
        dao.save(
            url=url,
            filename=os.path.basename(actual_path),
            title=info.get("title"),
            uploader=info.get("uploader") or info.get("creator"),
            duration=info.get("duration"),
            file_size=file_size,
            username=user,
        )
        media = "video/mp4" if ext in ("mp4", "webm", "mkv", "m4a") else "image/jpeg"
        return FileResponse(actual_path, filename=f"{safe_title}.{ext}", media_type=media)
    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e).split("\n")[0] if str(e) else "Error al descargar."
        if "No video formats" in err_msg or "No video format" in err_msg:
            # Fallback: pin solo imagen; obtener imagen desde la página (og:image)
            result = await _download_pin_image_fallback(url, filepath)
            if result:
                actual_path, ext, safe_title = result
                safe_title = (safe_title or "pin").replace("/", "-").strip() or "pin"
                file_size = os.path.getsize(actual_path)
                dao = DownloadDAO()
                dao.save(
                    url=url,
                    filename=os.path.basename(actual_path),
                    title=safe_title,
                    uploader=None,
                    duration=None,
                    file_size=file_size,
                    username=user,
                )
                media = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                return FileResponse(actual_path, filename=f"{safe_title}.{ext}", media_type=media)
        return JSONResponse({"error": err_msg}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)[:200]}"}, status_code=500)
