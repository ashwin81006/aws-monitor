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
    """
    summary_table = []
    if os.path.exists(MODEL_COMPARISON_PATH):
        df = pd.read_csv(MODEL_COMPARISON_PATH)
        summary_table = df.to_dict(orient="records")

    detailed_metrics = {}
    if os.path.exists(MODEL_METRICS_PATH):
        with open(MODEL_METRICS_PATH, "r") as f:
            detailed_metrics = json.load(f)

    return {
        "primary_model": "Isolation Forest",
        "features_count": 31,
        "comparison_table": summary_table,
        "detailed_metrics": detailed_metrics
    }
