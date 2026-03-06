import os

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.margen_dao import MargenDAO

app = FastAPI(root_path="/margen")
templates = Jinja2Templates(directory="app/templates")
_portal = (os.environ.get("PORTAL_URL") or "/").rstrip("/")
templates.env.globals["portal_url"] = _portal + "/" if _portal != "/" else "/"
templates.env.globals["favicon_url"] = _portal + "/static/favicon.png"


def _format_co(value, decimals=2):
    """Formato Colombia: miles con punto, decimales con coma."""
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


def _calcular(coste_producto: float, envio: float, fee_pct: float, impuesto_pct: float, precio_venta: float):
    coste_total = coste_producto + envio
    costes_extra = coste_total * (fee_pct / 100 + impuesto_pct / 100)
    precio_minimo = coste_total + costes_extra
    margen_neto = precio_venta - precio_minimo
    margen_pct = (margen_neto / precio_venta * 100) if precio_venta else 0
    return margen_neto, margen_pct, precio_minimo


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = MargenDAO()
    historial = dao.get_recent(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "historial": historial, "user": user})


@app.post("/calcular")
async def calcular(
    request: Request,
    coste_producto: float = Form(...),
    envio: float = Form(0),
    fee_plataforma_pct: float = Form(0),
    impuesto_pct: float = Form(0),
    precio_venta: float = Form(...),
    cpa: float = Form(0),
    user=Depends(verify_token),
):
    coste_producto = max(0, coste_producto)
    envio = max(0, envio)
    fee_plataforma_pct = max(0, min(100, fee_plataforma_pct))
    impuesto_pct = max(0, min(100, impuesto_pct))
    precio_venta = max(0, precio_venta)
    cpa = max(0, cpa)
    margen_neto, margen_pct, _ = _calcular(coste_producto, envio, fee_plataforma_pct, impuesto_pct, precio_venta)
    dao = MargenDAO()
    dao.save(
        coste_producto=coste_producto,
        envio=envio,
        fee_pct=fee_plataforma_pct,
        impuesto_pct=impuesto_pct,
        precio_venta=precio_venta,
        margen_neto=margen_neto,
        margen_pct=margen_pct,
        username=user,
        cpa=cpa,
    )
    return RedirectResponse(url=".", status_code=302)
