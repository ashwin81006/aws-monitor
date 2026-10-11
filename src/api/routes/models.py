import os
import json
import pandas as pd
from fastapi import APIRouter
from typing import Dict, Any

from ..config import MODEL_COMPARISON_PATH, MODEL_METRICS_PATH

router = APIRouter(prefix="/api/v1/models", tags=["Model Benchmark & Comparison"])


@router.get("/benchmark")
def get_model_benchmark_comparison() -> Dict[str, Any]:
    """
    Returns standardized benchmark comparison metrics across:
    1. Isolation Forest (Primary Model)
    2. Local Outlier Factor - LOF (Density Benchmark)
    3. One-Class SVM (Margin Benchmark)

    Returns authentic measured metrics from disk. If artifacts are unavailable,
    reports clear UNAVAILABLE status rather than fabricating synthetic measurements.
    """
    summary_table = []
    benchmark_available = False

    if os.path.exists(MODEL_COMPARISON_PATH):
        try:
            df = pd.read_csv(MODEL_COMPARISON_PATH)
            summary_table = df.to_dict(orient="records")
            benchmark_available = True
        except Exception:
            summary_table = []

    detailed_metrics = {}
    if os.path.exists(MODEL_METRICS_PATH):
        try:
            with open(MODEL_METRICS_PATH, "r") as f:
                detailed_metrics = json.load(f)
        except Exception:
            detailed_metrics = {}

    if not benchmark_available:
        return {
            "status": "UNAVAILABLE",
            "message": "Model comparison benchmark artifacts not found. Please execute model comparison pipeline.",
            "primary_model": "Isolation Forest",
            "features_count": 31,
            "comparison_table": [],
            "models": [],
            "detailed_metrics": {}
        }

    return {
        "status": "AVAILABLE",
        "primary_model": "Isolation Forest",
        "artifact_source": MODEL_COMPARISON_PATH,
        "features_count": 31,
        "comparison_table": summary_table,
        "models": summary_table,
        "detailed_metrics": detailed_metrics
    }
