from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TelemetryPointInput(BaseModel):
    timestamp: Optional[str] = Field(None, description="ISO timestamp (YYYY-MM-DD HH:MM:SS)")
    
    # Core temperature readings (°C)
    temp_2m: float = Field(..., description="Air temperature at 2m height (°C)")
    temp_4m: float = Field(..., description="Air temperature at 4m height (°C)")
    temp_8m: float = Field(..., description="Air temperature at 8m height (°C)")
    
    # Core relative humidity readings (%)
    rh_2m: float = Field(..., description="Relative humidity at 2m height (%)")
    rh_4m: float = Field(..., description="Relative humidity at 4m height (%)")
    rh_8m: float = Field(..., description="Relative humidity at 8m height (%)")
    
    # Surface & diagnostics
    pressure: float = Field(..., description="Atmospheric barometric pressure (mbar)")
    battery_voltage: float = Field(..., description="Station lead-acid battery voltage (V)")
    wind_speed_10m: Optional[float] = Field(0.0, description="Wind speed at 10m (m/s)")
    rainfall: Optional[float] = Field(0.0, description="Rainfall precipitation (mm)")

    # Optional previous step for dynamic rates calculation
    prev_temp_2m: Optional[float] = None
    prev_temp_4m: Optional[float] = None
    prev_temp_8m: Optional[float] = None
    prev_rh_2m: Optional[float] = None
    prev_rh_4m: Optional[float] = None
    prev_rh_8m: Optional[float] = None
    prev_pressure: Optional[float] = None
    prev_battery_voltage: Optional[float] = None


class TelemetryInferenceResponse(BaseModel):
    timestamp: str
    classification: str
    anomaly_probability: float
    fused_anomaly_score: Optional[float] = None
    confidence: float
    severity: str
    probable_root_cause: str
    root_cause: Optional[str] = None
    affected_sensors: List[str]
    is_anomaly: bool
    if_score: float
    if_outlier: bool
    evidence_breakdown: Dict[str, Any]
    explanation: str



class TelemetryHistoryPoint(BaseModel):
    timestamp: str
    temp_2m: Optional[float] = None
    temp_4m: Optional[float] = None
    temp_8m: Optional[float] = None
    rh_2m: Optional[float] = None
    rh_4m: Optional[float] = None
    rh_8m: Optional[float] = None
    pressure: Optional[float] = None
    battery_voltage: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    rainfall: Optional[float] = None
    is_anomaly: bool = False
    fused_score: Optional[float] = None
    classification: Optional[str] = None


class TelemetryHistoryResponse(BaseModel):
    total_points: int
    downsampled_points: int
    downsample_factor: int
    series: List[TelemetryHistoryPoint]
