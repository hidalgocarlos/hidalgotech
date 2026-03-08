import json
import os
import re
import uuid

import httpx
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from instagrapi import Client
from instagrapi.exceptions import InstagramException, LoginRequired

from .auth import verify_token
from .dao.download_dao import DownloadDAO

app = FastAPI(root_path="/instagram")
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["portal_url"] = "/"
templates.env.globals["favicon_url"] = "/static/favicon.png"

DOWNLOAD_DIR = "/app/data/downloads"
SESSION_FILE = "/app/data/session.json"
COOKIES_FILE = "/app/data/cookies.txt"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _get_instagrapi_client() -> Client:
    """Crea un cliente de instagrapi con sesión persistente si existe."""
    cl = Client()
    if os.path.isfile(SESSION_FILE):
        try:
            with open(SESSION_FILE) as f:
                session = json.load(f)
            cl.set_settings(session)
        except Exception:
            pass
    return cl


def _save_session(cl: Client):
    """Guarda la sesión del cliente en JSON."""
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(cl.get_settings(), f)
    except Exception:
        pass


def _extract_media_id(url: str) -> str | None:
    """Extrae el media_id de una URL de Instagram."""
    patterns = [
        r"(?:instagram\.com|instagr\.am)(?:/[^/?]+)?/(?:reel|p|stories)/([^/?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _detect_media_type(url: str) -> str:
    if "/reel/" in url or "/reels/" in url:
        return "Reel"
    if "/stories/" in url:
        return "Historia"
    return "Post"


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
    """Obtiene información del medio (reel, historia o post)."""
    if not url.strip():
        return JSONResponse({"error": "Escribe una URL de Instagram."}, status_code=400)
    if "instagram.com" not in url and "instagr.am" not in url:
        return JSONResponse({"error": "Solo se admiten enlaces de Instagram (instagram.com)."}, status_code=400)

    media_id = _extract_media_id(url)
    if not media_id:
        return JSONResponse({"error": "No se pudo extraer el ID del enlace."}, status_code=400)

    try:
        cl = _get_instagrapi_client()
        media = cl.media_info(media_id)
        if not media:
            return JSONResponse({"error": "No se pudo obtener información del enlace. ¿Es público?"}, status_code=400)

        media_type = _detect_media_type(url)
        thumbnail = None
        if media.thumbnail_url:
            thumbnail = media.thumbnail_url
        elif hasattr(media, "image_versions2") and media.image_versions2:
            candidates = media.image_versions2.get("candidates", [])
            if candidates:
                thumbnail = candidates[0].url

        return JSONResponse(
            {
                "title": getattr(media.user, "username", "—"),
                "thumbnail": thumbnail,
                "type": media_type,
                "uploader": getattr(media.user, "full_name", "—") or getattr(media.user, "username", "—"),
            }
        )
    except LoginRequired:
        return JSONResponse(
            {"error": "El contenido es privado o requiere iniciar sesión. Prueba subiendo cookies.txt arriba."},
            status_code=400,
        )
    except InstagramException as e:
        msg = str(e)
        if "not found" in msg.lower() or "private" in msg.lower():
            msg = "El contenido es privado, no existe o requiere iniciar sesión."
        return JSONResponse({"error": msg[:200]}, status_code=400)
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
    if not url.strip():
        return JSONResponse({"error": "Escribe una URL de Instagram."}, status_code=400)
    if "instagram.com" not in url and "instagr.am" not in url:
        return JSONResponse({"error": "Solo se admiten enlaces de Instagram (instagram.com)."}, status_code=400)

    media_id = _extract_media_id(url)
    if not media_id:
        return JSONResponse({"error": "No se pudo extraer el ID del enlace."}, status_code=400)

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    try:
        cl = _get_instagrapi_client()
        media = cl.media_info(media_id)
        if not media:
            return JSONResponse({"error": "No se pudo obtener el video."}, status_code=400)

        # Descargar el video: preferir video_url (más fiable) y fallback a instagrapi por pk
        video_url = getattr(media, "video_url", None)
        if not video_url and getattr(media, "resources", None):
            for r in media.resources or []:
                video_url = getattr(r, "video_url", None)
                if video_url:
                    break

        if video_url:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                r = await client.get(
                    video_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/119.0"},
                )
                r.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(r.content)
        else:
            media_pk = getattr(media, "pk", None) or getattr(media, "id", None)
            if media_pk is not None:
                cl.video_download(media_pk, DOWNLOAD_DIR)
                # instagrapi guarda con nombre automático; buscar el más reciente y renombrar
                downloads = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".mp4")]
                if downloads:
                    by_mtime = sorted(downloads, key=lambda f: os.path.getmtime(os.path.join(DOWNLOAD_DIR, f)), reverse=True)
                    os.rename(os.path.join(DOWNLOAD_DIR, by_mtime[0]), filepath)
            else:
                return JSONResponse({"error": "No se encontró video para descargar en este enlace."}, status_code=400)

        if not os.path.isfile(filepath):
            return JSONResponse({"error": "La descarga no generó ningún archivo. Prueba otro enlace."}, status_code=500)

        file_size = os.path.getsize(filepath)
        media_type = _detect_media_type(url)
        uploader_name = getattr(media.user, "username", "—")
        safe_title = (uploader_name or "video").replace("/", "-").strip() or "video"

        dao = DownloadDAO()
        dao.save(
            url=url,
            filename=filename,
            title=uploader_name,
            uploader=getattr(media.user, "full_name", uploader_name),
            duration=getattr(media, "video_duration", None),
            file_size=file_size,
            media_type=media_type,
            username=user,
        )
        return FileResponse(filepath, filename=f"{safe_title}.mp4", media_type="video/mp4")
    except LoginRequired:
        return JSONResponse(
            {"error": "El contenido es privado o requiere iniciar sesión. Prueba subiendo cookies.txt."},
            status_code=400,
        )
    except InstagramException as e:
        msg = str(e)
        if "not found" in msg.lower() or "private" in msg.lower():
            msg = "El contenido es privado, no existe o requiere iniciar sesión."
        return JSONResponse({"error": msg[:200]}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)[:200]}"}, status_code=500)


@app.post("/upload-cookies")
async def upload_cookies(file: UploadFile = File(...), user=Depends(verify_token)):
    if not file.filename:
        return JSONResponse(
            {"error": "Sube un archivo (.txt Netscape o .json sesión)"},
            status_code=400,
        )

    filename_lower = file.filename.lower()
    content = await file.read()

    try:
        if filename_lower.endswith(".json"):
            # Sesión JSON
            session_data = json.loads(content)
            with open(SESSION_FILE, "w") as f:
                json.dump(session_data, f)
            return JSONResponse({"ok": True, "message": "Sesión importada. Útil para acceso a contenido privado."})
        elif filename_lower.endswith(".txt"):
            # Cookies Netscape
            with open(COOKIES_FILE, "wb") as f:
                f.write(content)
            return JSONResponse({"ok": True, "message": "Cookies guardadas. Útil para historias privadas."})
        else:
            return JSONResponse(
                {"error": "Sube un archivo .txt (Netscape) o .json (sesión)"},
                status_code=400,
            )
    except json.JSONDecodeError:
        return JSONResponse({"error": "Archivo JSON inválido."}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Error al procesar archivo: {str(e)[:100]}"}, status_code=500)
