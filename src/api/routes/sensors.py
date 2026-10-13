from fastapi import APIRouter

from ..schemas.health import SensorHealthResponse
from ..services.health_service import health_service

router = APIRouter(prefix="/api/v1/sensors", tags=["Sensor Health & Reliability"])


@router.get("/health", response_model=SensorHealthResponse)
def get_sensors_health():
    return health_service.get_sensor_health()
