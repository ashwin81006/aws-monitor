"""
Isolation Forest Model Wrapper.
Calls the in-memory train_models pipeline.
"""

from .train_models import train_models


def run_isolation_forest():
    model_if, _, _, scaler, _, _ = train_models()
    return model_if, scaler


if __name__ == "__main__":
    run_isolation_forest()