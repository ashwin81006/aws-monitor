from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TelemetryPointInput(BaseModel):
    timestamp: Optional[str] = Field(None, description="ISO timestamp (YYYY-MM-DD HH:MM:SS)")
    
    # Core SIH Parameters
    temperature: Optional[float] = Field(None, description="Air temperature (°C)")
    humidity: Optional[float] = Field(None, description="Relative humidity (%)")
    pressure: Optional[float] = Field(985.0, description="Atmospheric barometric pressure (hPa/mbar)")
    
    # Backward compatibility aliases for multi-height clients
    temp_2m: Optional[float] = None
    temp_4m: Optional[float] = None
    temp_8m: Optional[float] = None
    rh_2m: Optional[float] = None
    rh_4m: Optional[float] = None
    rh_8m: Optional[float] = None
    battery_voltage: Optional[float] = 12.8
    wind_speed_10m: Optional[float] = 0.0
    rainfall: Optional[float] = 0.0

    def get_temperature(self) -> float:
        if self.temperature is not None:
            return self.temperature
        return self.temp_2m if self.temp_2m is not None else 28.5

    def get_humidity(self) -> float:
        if self.humidity is not None:
            return self.humidity
        return self.rh_2m if self.rh_2m is not None else 65.0

    def get_pressure(self) -> float:
        return self.pressure if self.pressure is not None else 985.0


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

    # Self-healing attributes
    corrected_temperature: Optional[float] = None
    corrected_humidity: Optional[float] = None
    corrected_pressure: Optional[float] = None
    is_healed: Optional[bool] = False
    healing_method: Optional[str] = None


class TelemetryHistoryPoint(BaseModel):
    timestamp: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    temp_2m: Optional[float] = None
    temp_4m: Optional[float] = None
    temp_8m: Optional[float] = None
    rh_2m: Optional[float] = None
    rh_4m: Optional[float] = None
    rh_8m: Optional[float] = None
    battery_voltage: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    rainfall: Optional[float] = None
    fused_score: Optional[float] = None
    is_anomaly: Optional[bool] = False
    severity: Optional[str] = "NOMINAL"


class TelemetryHistoryResponse(BaseModel):
    total_points: int
    downsampled_points: int
    downsample_factor: int
    series: List[TelemetryHistoryPoint]
