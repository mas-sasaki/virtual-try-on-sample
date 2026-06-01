from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pathlib

from app.routers import garments, upload, tryon

app = FastAPI(title="Virtual Try-On API", version="0.1.0")

app.include_router(garments.router)
app.include_router(upload.router)
app.include_router(tryon.router)

_templates = Jinja2Templates(directory=str(pathlib.Path(__file__).parent / "templates"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return _templates.TemplateResponse("index.html", {"request": request})
