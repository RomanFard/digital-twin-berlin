from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter(tags=["dashboard"])

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


@router.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))


@router.get("/static/{filename:path}")
def static_file(filename: str):
    filepath = os.path.join(STATIC_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    return {"error": "File not found"}