from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SensorHealthItem(BaseModel):
    sensor_id: str
    display_name: str
    unit: str
    current_health: float
    historical_min_health: float
    total_faults: int
    total_warnings: int
    clean_steps: int
    reliability_30d_pct: float
    grade: str
    status: str


class SensorHealthResponse(BaseModel):
    station_id: str
    overall_station_health: float
    overall_station_grade: str
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
