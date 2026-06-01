import pathlib

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse

from app.routers import garments, upload, tryon

app = FastAPI(title="Virtual Try-On API", version="0.1.0")

app.include_router(garments.router)
app.include_router(upload.router)
app.include_router(tryon.router)

_INDEX_HTML = pathlib.Path(__file__).parent / "templates" / "index.html"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(_INDEX_HTML)
