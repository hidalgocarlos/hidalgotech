from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .auth import verify_token
from .dao.item_dao import ItemDAO

# Change root_path to your app path, e.g. "/myapp"
app = FastAPI(root_path="/template")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(verify_token)):
    dao = ItemDAO()
    items = dao.get_all(limit=20)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "items": items, "user": user},
    )


@app.post("/add")
async def add_item(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    user=Depends(verify_token),
):
    dao = ItemDAO()
    dao.create(name=name, description=description or None)
    # Redirect to this app's root (change /template/ if you use another path)
    return RedirectResponse(url="/template/", status_code=302)
