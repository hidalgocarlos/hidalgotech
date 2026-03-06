import os

import httpx
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.conversion_dao import ConversionDAO

TRM_API_URL = "https://co.dolarapi.com/v1/trm"

app = FastAPI(root_path="/moneda")
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


@app.get("/api/trm")
async def get_trm(user=Depends(verify_token)):
    """Obtiene la TRM del dólar (Colombia) del día desde API externa."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(TRM_API_URL)
            r.raise_for_status()
            data = r.json()
            valor = float(data.get("valor", 0))
            fecha = data.get("fechaActualizacion", "")
            if valor <= 0:
                return {"ok": False, "error": "TRM no disponible"}
            return {"ok": True, "trm": valor, "fecha": fecha}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = ConversionDAO()
    historial = dao.get_recent(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "historial": historial, "user": user})


@app.post("/convertir")
async def convertir(
    request: Request,
    from_currency: str = Form("USD"),
    to_currency: str = Form("COP"),
    rate: float = Form(...),
    amount: float = Form(...),
    user=Depends(verify_token),
):
    from_currency = from_currency.upper().strip() or "USD"
    to_currency = to_currency.upper().strip() or "COP"
    rate = max(0.00001, rate)
    amount = max(0, amount)
    result = round(amount * rate, 2)
    dao = ConversionDAO()
    dao.save(
        from_currency=from_currency,
        to_currency=to_currency,
        rate=rate,
        amount=amount,
        result=result,
        username=user,
    )
    return RedirectResponse(url=".", status_code=302)
