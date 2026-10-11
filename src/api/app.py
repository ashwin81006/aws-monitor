import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.api.routes import (
    health,
    telemetry,
    anomalies,
    sensors,
    explainability,
    models,
)

app = FastAPI(
    title="AWS Monitor - Intelligent Anomaly Detection API",
    description=(
        "Production-grade REST API for Automatic Weather Station (AWS) telemetry quality control, "
        "real-time multi-source Bayesian evidence fusion, parameter-level dynamic reliability, "
        "and TreeSHAP model explainability.\n\n"
        "Authors: G. Ashwin Siva (24PD11) & Hariharan. V (24PD14)"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for .NET MAUI desktop app, web dashboards, and mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all modular route handlers
app.include_router(health.router)
app.include_router(telemetry.router)
app.include_router(anomalies.router)
app.include_router(sensors.router)
app.include_router(explainability.router)
app.include_router(models.router)


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

