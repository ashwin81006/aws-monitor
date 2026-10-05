import os
import sys
import subprocess


steps = [
    (
        "1/9",
        "Inspecting dataset",
        "src/exploration/inspect_dataset.py"
    ),
    (
        "2/9",
        "Analyzing values",
        "src/exploration/analyze_values.py"
    ),
    (
        "3/9",
        "Cleaning data",
        "src/preprocessing/clean_aws.py"
    ),
    (
        "4/9",
        "Running EDA summary",
        "src/exploration/eda_summary.py"
    ),
    (
        "5/9",
        "Building features",
        "src/features/build_features.py"
    ),
    (
        "6/9",
        "Selecting ML features",
        "src/ml/select_feature.py"
    ),
    (
        "7/9",
        "Splitting train/test data",
        "src/ml/split_data.py"
    ),
    (
        "8/9",
        "Preparing ML data",
        "src/ml/prepare_ml_data.py"
    ),
    (
        "9/9",
        "Training Isolation Forest",
        "src/ml/isolation_forest.py"
    )
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
        print(
            "ERROR: Raw dataset not found:"
        )
        print(input_file)
        print(
            "\nPlace your dataset at:"
        )
        print(
            "data/raw/aws_dataset.csv"
        )
        sys.exit(1)

    print("=" * 60)
    print("             WEATHER SENSE PIPELINE")
    print("=" * 60)

    print(
        "\nRaw dataset:",
        input_file
    )

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

    print("\nGenerated anomaly results:")
    print("data/processed/aws_if_results.csv")

    print("\nThe model is ready for the next detection stages.")


if __name__ == "__main__":
    main()