from fastapi import APIRouter

from ..schemas.health import SensorHealthResponse
from ..services.health_service import health_service

router = APIRouter(prefix="/api/v1/sensors", tags=["Sensor Health & Reliability"])


@router.get("/health", response_model=SensorHealthResponse)
def get_sensors_health():
    """
    Returns parameter-level dynamic reliability metrics for all 10 monitored channels,
    including current health (0-100), historical minimum, 30-day windowed reliability %,
    fault count, warning count, and operational grade.
    """
    return health_service.get_sensor_health()
