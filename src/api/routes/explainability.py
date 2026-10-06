from fastapi import APIRouter, HTTPException

from ..schemas.explainability import (
    ShapGlobalImportanceResponse,
    ShapEventExplanationResponse,
)
from ..services.explainability_service import explainability_service

router = APIRouter(prefix="/api/v1/explainability", tags=["Model Explainability (SHAP)"])


@router.get("/global-importance", response_model=ShapGlobalImportanceResponse)
def get_global_feature_importance():
    """
    Returns global feature importance rankings computed across the anomaly cohort by TreeSHAP.
    Formatted for horizontal bar and ranking charts in LiveCharts2 and Recharts.
    """
    return explainability_service.get_global_importance()


@router.get("/events/{event_id}", response_model=ShapEventExplanationResponse)
def get_event_shap_explanation(event_id: int):
    """
    Returns local TreeSHAP feature attributions and waterfall data for a specific diagnosed anomaly event.
    Explains exactly which features drove the model prediction and by how much.
    """
    res = explainability_service.get_event_explanation(event_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"SHAP explanation for event #{event_id} not found.")
    return res
