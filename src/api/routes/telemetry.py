from fastapi import APIRouter, Query
from typing import Optional

from ..schemas.telemetry import (
    TelemetryPointInput,
    TelemetryInferenceResponse,
    TelemetryHistoryResponse,
)
from ..services.inference_service import inference_service
from ..services.telemetry_service import telemetry_service

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry & Streaming Inference"])


@router.post("/stream-point", response_model=TelemetryInferenceResponse)
def stream_single_observation(payload: TelemetryPointInput):
    return inference_service.infer_point(payload)


@router.get("/history", response_model=TelemetryHistoryResponse)
def get_telemetry_history(
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    downsample_factor: int = Query(4, ge=1, le=50)
):
    return telemetry_service.get_history(start_time=start_time, end_time=end_time, downsample_factor=downsample_factor)
