from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import Optional, Dict, Any
import pandas as pd
import io

from ..schemas.telemetry import (
    TelemetryPointInput,
    TelemetryInferenceResponse,
    TelemetryHistoryResponse,
)
from ..services.inference_service import inference_service
from ..services.telemetry_service import telemetry_service
from ..services.dataset_processor import process_and_activate_dataset

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry & Streaming Inference"])


@router.post("/stream-point", response_model=TelemetryInferenceResponse)
def stream_single_observation(payload: TelemetryPointInput):
    """
    Real-time streaming inference for an individual AWS telemetry reading.
    Computes 31 domain features, passes through RobustScaler, runs Isolation Forest,
    cross-height consensus, temporal jump-rebound, battery power state, and Bayesian fusion.
    """
    return inference_service.infer_point(payload)


@router.get("/history", response_model=TelemetryHistoryResponse)
def get_telemetry_history(
    start_time: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD HH:MM:SS)"),
    end_time: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD HH:MM:SS)"),
    downsample_factor: int = Query(4, ge=1, le=50, description="Downsample stride (preserves all anomalies)")
):
    """
    Returns time-series telemetry formatted for LiveCharts2 and Recharts.
    Includes smart downsampling to guarantee 60 FPS client rendering without losing anomaly spikes.
    """
    return telemetry_service.get_history(start_time=start_time, end_time=end_time, downsample_factor=downsample_factor)


MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB limit


@router.post("/upload")
async def upload_telemetry_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Batch CSV upload endpoint for automated ingestion, schema validation, feature extraction,
    multi-height lapse gradient verification, Isolation Forest inference, and full dashboard activation.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds maximum allowed limit of 50 MB.")

    try:
        df = pd.read_csv(io.StringIO(content.decode("utf-8", errors="replace")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    if len(df) == 0:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")

    try:
        return process_and_activate_dataset(df, file.filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset processing failure: {str(e)}")


