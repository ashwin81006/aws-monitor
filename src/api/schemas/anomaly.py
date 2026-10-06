from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AnomalyEvent(BaseModel):
    event_id: int
    start_time: str
    end_time: str
    duration_minutes: float
    observations: int
    mean_fused_score: float
    peak_fused_score: float
    target_sensor: str
    candidate_class: str
    severity: str
    confidence: float
    probable_root_cause: str


class AnomalyEventDetail(AnomalyEvent):
    evidence_breakdown: Dict[str, Any]
    affected_sensors: List[str]
    rule_flags: List[str]
    cross_sensor_delta: Optional[float] = None
    temporal_rate_max: Optional[float] = None
    battery_level: Optional[float] = None
    if_score: Optional[float] = None
    explanation: str
    top_shap_features: Optional[List[Dict[str, Any]]] = None


class AnomalyEventsResponse(BaseModel):
    total_events: int
    limit: int
    offset: int
    counts_by_category: Dict[str, int]
    counts_by_severity: Dict[str, int]
    events: List[AnomalyEvent]
