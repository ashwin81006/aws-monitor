from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from ..schemas.anomaly import AnomalyEventsResponse, AnomalyEventDetail
from ..services.anomaly_service import anomaly_service

router = APIRouter(prefix="/api/v1/anomalies", tags=["Anomalies & Diagnosed Events"])


@router.get("/events", response_model=AnomalyEventsResponse)
def get_anomaly_events(
    category: Optional[str] = Query(None, description="Category filter (e.g. PROBABLE_SENSOR_FAULT, POSSIBLE_WEATHER_EXTREME, UNCERTAIN, ALL)"),
    severity: Optional[str] = Query(None, description="Severity filter (e.g. CRITICAL, HIGH, MEDIUM, LOW, ALL)"),
    search: Optional[str] = Query(None, description="Search term across target sensor or root cause"),
    limit: int = Query(50, ge=1, le=500, description="Number of events to retrieve"),
    offset: int = Query(0, ge=0, description="Offset index for pagination")
):
    """
    Retrieves filterable, paginated anomaly events clustered by the Bayesian fusion engine.
    """
    return anomaly_service.get_events(
        category=category,
        severity=severity,
        search=search,
        limit=limit,
        offset=offset
    )


@router.get("/events/{event_id}", response_model=AnomalyEventDetail)
def get_event_detail(event_id: int):
    """
    Retrieves forensic evidence details for a single diagnosed anomaly event,
    including rule flags, tower divergence spread, temporal jump, battery voltage, and SHAP contributors.
    """
    detail = anomaly_service.get_event_detail(event_id=event_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Anomaly event with ID {event_id} not found.")
    return detail
