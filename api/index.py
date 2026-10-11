import os
import sys

# Ensure root workspace directory is in Python module search path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.responses import RedirectResponse
from src.api.app import app

# Catch Vercel rewritten paths and route them directly to Swagger documentation
@app.get("/api/index.py", include_in_schema=False)
@app.get("/api", include_in_schema=False)
@app.get("/api/", include_in_schema=False)
@app.get("/api/docs", include_in_schema=False)
def vercel_entrypoint_redirect():
    return RedirectResponse(url="/docs")

@app.get("/api/redoc", include_in_schema=False)
def vercel_redoc_redirect():
    return RedirectResponse(url="/redoc")
