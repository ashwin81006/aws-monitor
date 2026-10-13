from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from ..schemas.anomaly import AnomalyEventsResponse, AnomalyEventDetail
from ..services.anomaly_service import anomaly_service

router = APIRouter(prefix="/api/v1/anomalies", tags=["Anomalies & Diagnosed Events"])


@router.get("/events", response_model=AnomalyEventsResponse)
def get_anomaly_events(
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    return anomaly_service.get_events(
        category=category,
        severity=severity,
        search=search,
        limit=limit,
        offset=offset
    )


@router.get("/events/{event_id}", response_model=AnomalyEventDetail)
def get_event_detail(event_id: int):
    detail = anomaly_service.get_event_detail(event_id=event_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Anomaly event with ID {event_id} not found.")
    return detail
