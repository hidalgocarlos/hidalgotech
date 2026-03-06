import os

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.generacion_dao import GeneracionDAO
from .generador import REDES, generar

app = FastAPI(root_path="/hashtags")
templates = Jinja2Templates(directory="app/templates")
_portal = (os.environ.get("PORTAL_URL") or "/").rstrip("/")
templates.env.globals["portal_url"] = _portal + "/" if _portal != "/" else "/"
templates.env.globals["favicon_url"] = _portal + "/static/favicon.png"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = GeneracionDAO()
    historial = dao.get_recent(limit=50)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "historial": historial, "user": user, "redes": REDES},
    )


@app.post("/generar")
async def generar_post(
    request: Request,
    tema: str = Form(""),
    red: str = Form("instagram"),
    user=Depends(verify_token),
):
    tema = (tema or "").strip()
    if not tema:
        dao = GeneracionDAO()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "historial": dao.get_recent(limit=50),
                "user": user,
                "redes": REDES,
                "error": "Escribe un tema o palabra clave.",
            },
        )
    copy_texto, hashtags = generar(tema, red)
    dao = GeneracionDAO()
    dao.save(tema=tema, red=red, copy_texto=copy_texto, hashtags=hashtags, username=user)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "historial": dao.get_recent(limit=50),
            "user": user,
            "redes": REDES,
            "tema": tema,
            "red": red,
            "copy_result": copy_texto,
            "hashtags_result": hashtags,
        },
    )
