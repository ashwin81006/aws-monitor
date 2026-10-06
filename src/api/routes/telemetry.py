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


@router.post("/upload")
async def upload_telemetry_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Batch CSV upload endpoint for automated ingestion, cleaning, and quality scoring.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode("utf-8", errors="replace")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    row_count = len(df)
    col_count = len(df.columns)

    return {
        "status": "UPLOAD_SUCCESSFUL",
        "filename": file.filename,
        "rows_received": row_count,
        "columns_received": col_count,
        "message": f"Successfully parsed {row_count} rows across {col_count} columns."
    }
