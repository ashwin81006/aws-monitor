from fastapi import APIRouter
from typing import Dict, Any

from ..services.health_service import health_service
from ..schemas.health import StationSummaryResponse
from ..config import STATION_METADATA

router = APIRouter(tags=["System & Station Metadata"])


@router.get("/health")
@router.get("/api/v1/health")
def get_health() -> Dict[str, Any]:
    return {
        "status": "ONLINE",
        "service": "AWS Monitor - Anomaly Detection API",
        "station_id": STATION_METADATA["station_id"],
        "active_model": "Isolation Forest (31 Clean Domain Features)",
        "features_count": 31,
        "calibration": "Empirical Bayesian Multi-Source Evidence Fusion",
        "explainability": "TreeSHAP Local & Global Attributions"
    }


@router.get("/api/v1/station/summary", response_model=StationSummaryResponse)
def get_station_summary():
    return health_service.get_station_summary()
