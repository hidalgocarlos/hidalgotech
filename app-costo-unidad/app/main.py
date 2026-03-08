import os

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.costo_dao import CostoDAO

app = FastAPI(root_path="/costo-unidad")
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["portal_url"] = "/"
templates.env.globals["favicon_url"] = "/static/favicon.png"


def format_number_co_style(value, decimals=2):
    """
    Formats a number in Colombian style:
    - Dot (.) for thousands separator.
    - Comma (,) for decimal separator.
    - Returns '—' if the value is not a valid number.
    """
    if value is None:
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"

    # Standard formatting with comma for thousands, dot for decimals.
    s = f"{n:,.{decimals}f}"
    # Swap separators for Colombian style (e.g., 1,234.56 -> 1.234,56)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


templates.env.filters["format_co"] = format_number_co_style


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

    # Clean up the note: strip whitespace and treat empty strings as NULL
    cleaned_nota = nota.strip() if nota else ""
    nota_for_db = cleaned_nota if cleaned_nota else None

    dao = CostoDAO()
    dao.save(
        coste_total=coste_total,
        unidades=unidades,
        costo_por_unidad=costo_por_unidad,
        nota=nota_for_db,
        username=user,
    )
    return RedirectResponse(url=".", status_code=302)
