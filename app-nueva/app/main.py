from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Copiar auth.py desde cualquier aplicación existente y usar el mismo SECRET_KEY
# from .auth import verify_token

app = FastAPI(root_path="/nueva")  # Cambiar por el path de la app
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):  # , user=Depends(verify_token)
    return templates.TemplateResponse("index.html", {"request": request})
