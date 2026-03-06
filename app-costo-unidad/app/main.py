import os

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.costo_dao import CostoDAO

app = FastAPI(root_path="/costo-unidad")
templates = Jinja2Templates(directory="app/templates")
_portal = (os.environ.get("PORTAL_URL") or "/").rstrip("/")
templates.env.globals["portal_url"] = _portal + "/" if _portal != "/" else "/"
templates.env.globals["favicon_url"] = _portal + "/static/favicon.png"


def _format_co(value, decimals=2):
    if value is None:
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    s = f"{n:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


templates.env.filters["format_co"] = _format_co


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = CostoDAO()
    historial = dao.get_recent(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "historial": historial, "user": user})


@app.post("/calcular")
async def calcular(
    request: Request,
    coste_total: float = Form(...),
    unidades: int = Form(...),
    nota: str = Form(""),
    user=Depends(verify_token),
):
    coste_total = max(0, coste_total)
    unidades = max(1, int(unidades))
    costo_por_unidad = coste_total / unidades
    dao = CostoDAO()
    dao.save(
        coste_total=coste_total,
        unidades=unidades,
        costo_por_unidad=costo_por_unidad,
        nota=(nota or "").strip() or None,
        username=user,
    )
    return RedirectResponse(url=".", status_code=302)
