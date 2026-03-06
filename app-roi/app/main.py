import os

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.roi_dao import ROIDAO

app = FastAPI(root_path="/roi")
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
    dao = ROIDAO()
    historial = dao.get_recent(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "historial": historial, "user": user})


@app.post("/calcular")
async def calcular(
    request: Request,
    inversion: float = Form(...),
    ventas: float = Form(...),
    clics: int = Form(0),
    conversiones: int = Form(0),
    user=Depends(verify_token),
):
    inversion = max(0, inversion)
    ventas = max(0, ventas)
    clics = max(0, int(clics))
    conversiones = max(0, int(conversiones))
    roi_pct = ((ventas - inversion) / inversion * 100) if inversion else 0
    roas = (ventas / inversion) if inversion else 0
    cpc = (inversion / clics) if clics else None
    cpa = (inversion / conversiones) if conversiones else None
    dao = ROIDAO()
    dao.save(
        inversion=inversion,
        ventas=ventas,
        roi_pct=roi_pct,
        roas=roas,
        clics=clics or None,
        conversiones=conversiones or None,
        cpc=cpc,
        cpa=cpa,
        username=user,
    )
    return RedirectResponse(url=".", status_code=302)
