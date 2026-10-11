import os
import sys
import subprocess


# ==============================================================================
# AWS MONITOR: CONSOLIDATED END-TO-END AUTOMATED PIPELINE
# ==============================================================================
# 16 cleanly orchestrated, non-redundant, modular steps:
#   1. Preprocessing & Data Cleaning (src/preprocessing/clean_aws.py)
#   2. Exploratory Data Analysis & Profiling (src/exploration/eda_summary.py)
#   3. Feature Engineering (31 causal features: src/features/build_features.py)
#   4. ML Data Preparation (70/30 split, Imputation, RobustScaler: src/ml/prepare_ml_data.py)
#   5. ML Model: Isolation Forest (src/ml/isolation_forest.py)
#   6. ML Model: Local Outlier Factor (src/ml/local_outlier_factor.py)
#   7. ML Model: One-Class SVM (src/ml/one_class_svm.py)
#   8. Detection: Rule-based Quality Control (src/detection/rule_qc.py)
#   9. Detection: Empirical Threshold Calibration (src/detection/calibrate_thresholds.py)
#  10. Detection: Cross-Sensor Consistency Evidence (src/detection/cross_sensor_evidence.py)
#  11. Detection: Temporal Dynamic Evidence (src/detection/temporal_evidence.py)
#  12. Detection: Multi-Source Evidence Matrix (src/detection/build_evidence_matrix.py)
#  13. Detection: Event-Level Clustering & Root Cause Fusion (src/detection/event_fusion.py)
#  14. Controlled Synthetic Fault Validation (src/validation/run_validation.py)
#  15. Multi-Model Benchmark Comparison (src/ml/model_comparison.py)
#  16. Telemetry Model Explainability via TreeSHAP (src/explainability/shap_explainer.py)
# ==============================================================================

steps = [
    ("1/16", "Data Cleaning & Quality Flags", "src/preprocessing/clean_aws.py"),
    ("2/16", "EDA Summary & Quality Profiling", "src/exploration/eda_summary.py"),
    ("3/16", "Feature Engineering (Temporal, Cross-Sensor, Rolling, Repetition)", "src/features/build_features.py"),
    ("4/16", "ML Preparation, Train/Test Split & Robust Scaling", "src/ml/prepare_ml_data.py"),
    ("5/16", "Training Primary Model (Isolation Forest)", "src/ml/isolation_forest.py"),
    ("6/16", "Training Benchmark Model (Local Outlier Factor)", "src/ml/local_outlier_factor.py"),
    ("7/16", "Training Benchmark Model (One-Class SVM)", "src/ml/one_class_svm.py"),
    ("8/16", "Rule-based Quality Control (QC)", "src/detection/rule_qc.py"),
    ("9/16", "Calibrating Empirical Thresholds", "src/detection/calibrate_thresholds.py"),
    ("10/16", "Cross-Sensor Consistency Evidence", "src/detection/cross_sensor_evidence.py"),
    ("11/16", "Temporal Dynamic Evidence", "src/detection/temporal_evidence.py"),
    ("12/16", "Multi-Source Evidence Matrix Construction", "src/detection/build_evidence_matrix.py"),
    ("13/16", "Event-Level Clustering & Root Cause Fusion", "src/detection/event_fusion.py"),
    ("14/16", "Controlled Synthetic Fault Validation", "src/validation/run_validation.py"),
    ("15/16", "ML Model Comparison & Benchmarking", "src/ml/model_comparison.py"),
    ("16/16", "Telemetry Model Explainability (SHAP)", "src/explainability/shap_explainer.py")
]


def run_step(number, description, script):
    print("\n" + "=" * 65)
    print(f"[{number}] {description}")
    print("=" * 65)

    env = dict(os.environ, PYTHONPATH=".", PYTHONIOENCODING="utf-8")
    subprocess.run(
        [sys.executable, script],
        check=True,
        env=env
    )

    print(f"\n[{number}] {description} - DONE")


def main():
    input_file = "data/raw/aws_dataset.csv"

    if not os.path.exists(input_file):
        print("ERROR: Raw dataset not found:")
        print(input_file)
        print("\nPlace your dataset at:")
        print("data/raw/aws_dataset.csv")
        sys.exit(1)

    os.makedirs("models", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    print("=" * 65)
    print("              AWS MONITOR PIPELINE")
    print("=" * 65)
    print("\nRaw dataset:", input_file)

    for number, description, script in steps:
        if not os.path.exists(script):
            print(f"\nERROR: Script not found: {script}")
            sys.exit(1)

        run_step(number, description, script)

    print("\n" + "=" * 65)
    print("             PIPELINE COMPLETE")
    print("=" * 65)

    print("\nGenerated models & scaler:")
    print("  - models/scaler.pkl")
    print("  - models/train_medians.pkl")
    print("  - models/ml_feature_columns.json")
    print("  - models/isolation_forest.pkl")
    print("  - models/lof_model.pkl")
    print("  - models/ocsvm_model.pkl")

    print("\nGenerated calibration artifacts:")
    print("  - models/cross_sensor_thresholds.json")
    print("  - models/temporal_thresholds.json")

    print("\nGenerated primary pipeline datasets:")
    print("  - data/processed/aws_clean.csv")
    print("  - data/processed/aws_features.csv")
    print("  - data/processed/aws_train_scaled.csv")
    print("  - data/processed/aws_test_scaled.csv")
    print("  - data/processed/aws_evidence_matrix.csv")
    print("  - data/processed/aws_event_fusion.csv")

    print("\nGenerated validation artifacts:")
    print("  - data/processed/aws_fault_labels.csv")
    print("  - data/processed/aws_injected_events.csv")
    print("  - data/processed/aws_validation_event_evaluation.csv")
    print("  - data/processed/aws_validation_evaluation.csv")
    print("  - data/processed/aws_validation_metrics_summary.json")

    print("\nGenerated model comparison artifacts:")
    print("  - data/processed/aws_model_comparison.csv")
    print("  - data/processed/aws_fault_breakdown.csv")
    print("  - data/processed/aws_model_predictions.csv")
    print("  - data/processed/aws_model_comparison_metrics.json")

    print("\nGenerated explainability artifacts (SHAP):")
    print("  - data/processed/aws_shap_global_importance.csv")
    print("  - data/processed/aws_event_explanations.csv")
    print("  - data/processed/aws_event_explanations_summary.json")
    print("  - reports/figures/shap_global_importance.png")
    print("  - reports/figures/shap_summary_plot.png")
    print("  - reports/figures/shap_event_waterfall.png")

    print("\nThe complete anomaly detection pipeline has finished successfully.")


if __name__ == "__main__":
    main()