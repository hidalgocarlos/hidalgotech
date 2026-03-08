import os
import uuid

import yt_dlp
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.download_dao import DownloadDAO

app = FastAPI(root_path="/tiktok")
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["portal_url"] = "/"
templates.env.globals["favicon_url"] = "/static/favicon.png"

DOWNLOAD_DIR = "/app/data/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YDL_OPTS_BASE = {
    "quiet": True,
    "no_warnings": True,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _resolution_from_info(info: dict) -> str:
    width = info.get("width") or 0
    height = info.get("height") or 0
    if width and height:
        return f"{width}x{height}"
    return info.get("resolution") or ""


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
    url = (url or "").strip()
    if not url:
        return JSONResponse({"error": "Escribe una URL de TikTok."}, status_code=400)
    if "tiktok.com" not in url and "vm.tiktok.com" not in url:
        return JSONResponse({"error": "Solo se admiten enlaces de TikTok (tiktok.com o vm.tiktok.com)."}, status_code=400)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_BASE) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return JSONResponse({"error": "No se pudo obtener el video. Comprueba que el enlace sea correcto y público."}, status_code=400)
            thumb = info.get("thumbnail") or (info.get("thumbnails") or [{}])[-1].get("url") if info.get("thumbnails") else None
            return JSONResponse(
                {
                    "title": info.get("title"),
                    "thumbnail": thumb,
                    "duration": info.get("duration"),
                    "uploader": info.get("uploader"),
                    "resolution": _resolution_from_info(info),
                }
            )
    except yt_dlp.utils.DownloadError as e:
        msg = str(e).split("\n")[0] if str(e) else "Error al analizar el video."
        return JSONResponse({"error": msg}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)[:200]}"}, status_code=500)


@app.post("/download")
async def download(url: str = Form(...), user=Depends(verify_token)):
    url = (url or "").strip()
    if not url or ("tiktok.com" not in url and "vm.tiktok.com" not in url):
        return JSONResponse({"error": "URL de TikTok no válida."}, status_code=400)
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    ydl_opts = {
        **YDL_OPTS_BASE,
        "outtmpl": filepath,
        "format": "bestvideo+bestaudio/best[ext=mp4]/best",
        "merge_output_format": "mp4",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        if not info:
            return JSONResponse({"error": "No se pudo obtener el video."}, status_code=400)
        # yt-dlp a veces escribe con otra extensión; buscar el archivo generado
        actual_path = filepath
        if not os.path.isfile(actual_path):
            base = filepath.rsplit(".", 1)[0]
            for ext in (".mp4", ".webm", ".mkv", ".m4a"):
                if os.path.isfile(base + ext):
                    actual_path = base + ext
                    break
        if not os.path.isfile(actual_path):
            return JSONResponse({"error": "La descarga no generó ningún archivo. Prueba otro enlace."}, status_code=500)
        file_size = os.path.getsize(actual_path)
        safe_title = (info.get("title") or "video").replace("/", "-").strip() or "video"
        dao = DownloadDAO()
        dao.save(
            url=url,
            filename=os.path.basename(actual_path),
            title=info.get("title"),
            uploader=info.get("uploader"),
            duration=info.get("duration"),
            file_size=file_size,
            username=user,
        )
        return FileResponse(actual_path, filename=f"{safe_title}.mp4", media_type="video/mp4")
    except yt_dlp.utils.DownloadError as e:
        msg = str(e).split("\n")[0] if str(e) else "Error al descargar el video."
        return JSONResponse({"error": msg}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Error: {str(e)[:200]}"}, status_code=500)
