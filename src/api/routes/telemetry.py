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
    """
    Real-time streaming inference for an individual AWS telemetry reading.
    Executes thermodynamic sanity checks, rates of change, Isolation Forest,
    and self-healing reconstruction.
    """
    return inference_service.infer_point(payload)


@router.get("/history", response_model=TelemetryHistoryResponse)
def get_telemetry_history(
    start_time: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD HH:MM:SS)"),
    end_time: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD HH:MM:SS)"),
    downsample_factor: int = Query(4, ge=1, le=50, description="Downsample stride (preserves all anomalies)")
):
    """
    Returns time-series telemetry formatted for LiveCharts2 client rendering.
    Includes smart downsampling to guarantee smooth rendering without losing anomaly spikes.
    """
    return telemetry_service.get_history(start_time=start_time, end_time=end_time, downsample_factor=downsample_factor)
