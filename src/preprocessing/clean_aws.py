"""
Clean AWS Preprocessing wrapper.
Provides backward-compatible interface calling the in-memory preprocessor.
"""

from .preprocess import load_raw_dataset, preprocess_data, RAW_DATA_PATH


def run_cleaning(input_path=None, output_path=None):
    raw_df = load_raw_dataset(input_path)
    flagged_df, clean_df = preprocess_data(raw_df)
    if output_path:
        clean_df.to_csv(output_path, index=False)
    return clean_df


if __name__ == "__main__":
    df = run_cleaning()
    print(f"Clean AWS dataset ready with {len(df):,} rows.")