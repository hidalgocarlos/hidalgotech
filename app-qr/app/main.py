import base64
import io
import os

import qrcode
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.qr_dao import QRDAO

app = FastAPI(root_path="/qr")
templates = Jinja2Templates(directory="app/templates")
_portal = (os.environ.get("PORTAL_URL") or "/").rstrip("/")
templates.env.globals["portal_url"] = _portal + "/" if _portal != "/" else "/"
templates.env.globals["favicon_url"] = _portal + "/static/favicon.png"


def _make_qr_png(content: str, box_size: int = 8) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=box_size, border=4)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = QRDAO()
    historial = dao.get_recent(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "historial": historial, "user": user})


@app.post("/generate")
async def generate(
    request: Request,
    content: str = Form(""),
    user=Depends(verify_token),
):
    content = (content or "").strip()
    if not content:
        dao = QRDAO()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "historial": dao.get_recent(limit=50),
            "user": user,
            "error": "Escribe texto o una URL.",
        })
    dao = QRDAO()
    dao.save(content=content, username=user)
    png_bytes = _make_qr_png(content)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "historial": dao.get_recent(limit=50),
        "user": user,
        "qr_b64": base64.b64encode(png_bytes).decode(),
        "content": content,
    })


@app.get("/image")
async def qr_image(content: str = "", user=Depends(verify_token)):
    content = (content or "").strip() or "https://hidalgotech.com"
    png_bytes = _make_qr_png(content)
    return Response(content=png_bytes, media_type="image/png")
