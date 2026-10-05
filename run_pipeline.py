import os
import sys
import subprocess


steps = [
    ("1/15", "Inspecting dataset", "src/exploration/inspect_dataset.py"),
    ("2/15", "Analyzing values", "src/exploration/analyze_values.py"),
    ("3/15", "Cleaning data", "src/preprocessing/clean_aws.py"),
    ("4/15", "Running EDA summary", "src/exploration/eda_summary.py"),
    ("5/15", "Building features", "src/features/build_features.py"),
    ("6/15", "Selecting ML features", "src/ml/select_feature.py"),
    ("7/15", "Splitting train/test data", "src/ml/split_data.py"),
    ("8/15", "Preparing ML data", "src/ml/prepare_ml_data.py"),
    ("9/15", "Training Isolation Forest", "src/ml/isolation_forest.py"),

    ("10/15", "Running rule-based QC", "src/detection/rule_qc.py"),
    ("11/15", "Calibrating thresholds", "src/detection/calibrate_thresholds.py"),
    ("12/15", "Running cross-sensor evidence", "src/detection/cross_sensor_evidence.py"),
    ("13/15", "Running temporal evidence", "src/detection/temporal_evidence.py"),
    ("14/15", "Building evidence matrix", "src/detection/build_evidence_matrix.py"),
    ("15/15", "Running event-level fusion", "src/detection/event_fusion.py")
]

def run_step(number, description, script):

    print("\n" + "=" * 60)
    print(f"[{number}] {description}")
    print("=" * 60)

    subprocess.run(
        [sys.executable, script],
        check=True
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


    print("=" * 60)
    print("             WEATHER SENSE PIPELINE")
    print("=" * 60)

    print("\nRaw dataset:", input_file)


    for number, description, script in steps:

        if not os.path.exists(script):

            print(
                f"\nERROR: Script not found: {script}"
            )

            sys.exit(1)

        run_step(
            number,
            description,
            script
        )


    print("\n" + "=" * 60)
    print("             PIPELINE COMPLETE")
    print("=" * 60)


    print("\nGenerated model:")
    print("models/isolation_forest.pkl")


    print("\nGenerated calibration artifacts:")
    print("models/cross_sensor_thresholds.json")
    print("models/temporal_thresholds.json")


    print("\nGenerated ML anomaly results:")
    print("data/processed/aws_if_results.csv")


    print("\nGenerated evidence matrix:")
    print("data/processed/aws_evidence_matrix.csv")



    print("\nGenerated final event classifications:")
    print("data/processed/aws_event_fusion.csv")


    print("\nThe complete anomaly detection pipeline has finished.")


if __name__ == "__main__":
    main()