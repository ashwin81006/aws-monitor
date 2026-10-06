import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.validation.inject_faults import inject_synthetic_faults
from src.validation.run_validation_pipeline import run_validation_pipeline
from src.validation.evaluate_validation import evaluate_validation

# ==============================================================================
# CONTROLLED SYNTHETIC FAULT VALIDATION RUNNER
# ==============================================================================
# Injects controlled synthetic faults, runs detection & evidence fusion,
# and evaluates multi-level precision, recall, latency, and fault diagnosis.
# ==============================================================================

def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else "isolation_forest"
    
    print("=" * 65)
    print("        AWS MONITOR - CONTROLLED FAULT VALIDATION")
    print("=" * 65)

    print("\n[1/3] Injecting controlled synthetic sensor faults...")
    inject_synthetic_faults()

    print(f"\n[2/3] Running detection & fusion pipeline with {model_name.upper()}...")
    run_validation_pipeline(model_name=model_name)

    print("\n[3/3] Evaluating precision, recall, F1, latency, and diagnosis...")
    display_name = "Isolation Forest" if model_name == "isolation_forest" else model_name.upper()
    evaluate_validation(model_name=display_name)

    print("\n" + "=" * 65)
    print("        CONTROLLED FAULT VALIDATION COMPLETED SUCCESSFULLY")
    print("=" * 65)


if __name__ == "__main__":
    main()
