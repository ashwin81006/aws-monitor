import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.api.routes import (
    health,
    telemetry,
    anomalies,
    sensors,
    models,
)

app = FastAPI(
    title="AWS Monitor - Intelligent Anomaly Detection API",
    description="Production-grade REST API for Automatic Weather Station (AWS) telemetry quality control, Isolation Forest anomaly detection, and thermodynamic self-healing.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(telemetry.router)
app.include_router(anomalies.router)
app.include_router(sensors.router)
app.include_router(models.router)


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
