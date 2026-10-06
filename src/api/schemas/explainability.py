from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ShapFeatureImportance(BaseModel):
    feature: str
    mean_abs_shap: float
    rank: int
    physical_domain: str


class ShapGlobalImportanceResponse(BaseModel):
    total_features_evaluated: int
    top_features: List[ShapFeatureImportance]


class ShapLocalAttribution(BaseModel):
    feature: str
    feature_value: float
    shap_value: float
    direction: str
    contribution_pct: float


class ShapEventExplanationResponse(BaseModel):
    event_id: int
    timestamp: str
    anomaly_score: float
    expected_base_value: float
    prediction_outcome: str
    top_contributors: List[ShapLocalAttribution]
    plain_english_summary: str
