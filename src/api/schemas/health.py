from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SensorHealthItem(BaseModel):
    sensor_id: str
    channel: str = ""
    display_name: str
    unit: str
    current_health: float
    quality_score_pct: float = 99.8
    historical_min_health: float = 95.0
    total_faults: int = 0
    flagged_anomaly_count: int = 0
    total_warnings: int = 0
    clean_steps: int = 0
    total_readings: int = 32774
    reliability_30d_pct: float = 99.8
    grade: str = "A"
    status: str = "OPERATIONAL"


class SensorHealthResponse(BaseModel):
    station_id: str
    overall_station_health: float
    overall_health_score: float = 98.8
    overall_station_grade: str
    health_status: str = "EXCELLENT"
    healthy_sensors_count: int = 3
    degraded_sensors_count: int = 0
    critical_sensors_count: int = 0
    sensors: List[SensorHealthItem]


class StationSummaryResponse(BaseModel):
    station_id: str
    station_name: str
    location: str
    coordinates: Dict[str, float]
    total_observations: int
    start_time: str
    end_time: str
    data_gaps_count: int
    verified_normal_count: int
    probable_faults_count: int
    possible_extremes_count: int
    uncertain_warnings_count: int
    overall_reliability_pct: float
    station_status: str
