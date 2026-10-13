import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.responses import RedirectResponse
from src.api.app import app


@app.get("/api/index.py", include_in_schema=False)
@app.get("/api", include_in_schema=False)
@app.get("/api/", include_in_schema=False)
@app.get("/api/docs", include_in_schema=False)
def vercel_entrypoint_redirect():
    return RedirectResponse(url="/docs")


@app.get("/api/redoc", include_in_schema=False)
def vercel_redoc_redirect():
    return RedirectResponse(url="/redoc")
