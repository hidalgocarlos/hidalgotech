import os
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.link_dao import LinkDAO

app = FastAPI(root_path="/utm")
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["portal_url"] = "/"
templates.env.globals["favicon_url"] = "/static/favicon.png"


def _build_utm_url(base_url: str, utm_source: str, utm_medium: str, utm_campaign: str,
                   utm_term: str, utm_content: str) -> str:
    base = (base_url or "").strip()
    if not base:
        return ""
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    params = {}
    if (utm_source or "").strip():
        params["utm_source"] = utm_source.strip()
    if (utm_medium or "").strip():
        params["utm_medium"] = utm_medium.strip()
    if (utm_campaign or "").strip():
        params["utm_campaign"] = utm_campaign.strip()
    if (utm_term or "").strip():
        params["utm_term"] = utm_term.strip()
    if (utm_content or "").strip():
        params["utm_content"] = utm_content.strip()
    if not params:
        return base
    sep = "&" if "?" in base else "?"
    return base + sep + urlencode(params)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = LinkDAO()
    links = dao.get_recent(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "links": links, "user": user})


@app.post("/utm")
async def build_utm(
    request: Request,
    base_url: str = Form(""),
    utm_source: str = Form(""),
    utm_medium: str = Form(""),
    utm_campaign: str = Form(""),
    utm_term: str = Form(""),
    utm_content: str = Form(""),
    user=Depends(verify_token),
):
    url = _build_utm_url(base_url, utm_source, utm_medium, utm_campaign, utm_term, utm_content)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "links": LinkDAO().get_recent(limit=50),
        "user": user,
        "utm_result": url,
    })


@app.post("/shorten")
async def shorten(
    request: Request,
    long_url: str = Form(...),
    slug: str = Form(""),
    user=Depends(verify_token),
):
    long_url = (long_url or "").strip()
    if not long_url:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "links": LinkDAO().get_recent(limit=50),
            "user": user,
            "short_error": "Escribe una URL.",
        })
    if not long_url.startswith(("http://", "https://")):
        long_url = "https://" + long_url
    dao = LinkDAO()
    try:
        link = dao.create(long_url=long_url, slug=slug or None, username=user)
    except ValueError as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "links": dao.get_recent(limit=50),
            "user": user,
            "short_error": str(e),
        })
    base = request.base_url
    short_url = f"{base.rstrip('/')}/r/{link.slug}"
    return templates.TemplateResponse("index.html", {
        "request": request,
        "links": dao.get_recent(limit=50),
        "user": user,
        "short_result": short_url,
    })


@app.get("/r/{slug}")
async def redirect_slug(slug: str):
    dao = LinkDAO()
    link = dao.get_by_slug(slug)
    if not link:
        return HTMLResponse("<h1>Enlace no encontrado</h1>", status_code=404)
    return RedirectResponse(link.long_url, status_code=302)
