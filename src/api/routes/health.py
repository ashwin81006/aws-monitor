from fastapi import APIRouter
from typing import Dict, Any

from ..services.health_service import health_service
from ..services.inference_service import inference_service
from ..schemas.health import StationSummaryResponse
from ..config import STATION_METADATA

router = APIRouter(tags=["System & Station Metadata"])


@router.get("/health")
@router.get("/api/v1/health")
def get_health() -> Dict[str, Any]:
    inf_status = inference_service.get_service_status()
    is_demo = (inf_status.get("mode") == "DEMO_FALLBACK")
    status_str = "DEGRADED" if is_demo else "ONLINE"

    return {
        "status": status_str,
        "mode": "DEMO_FALLBACK" if is_demo else "PRODUCTION",
        "service": "AWS Monitor - Anomaly Detection API",
        "station_id": STATION_METADATA["station_id"],
        "active_model": inf_status.get("loaded_model", "Isolation Forest"),
        "features_count": inf_status.get("features_count", 13),
        "calibration": "Calibrated with Thermodynamic Consistency",
        "explainability": "TreeSHAP Local & Global Attributions",
        "is_demo_mode": is_demo
    }


@router.get("/api/v1/station/summary", response_model=StationSummaryResponse)
def get_station_summary():
    return health_service.get_station_summary()
