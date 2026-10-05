import pandas as pd
import numpy as np

input_file = "data/processed/aws_ml_features.csv"
output_file = "data/processed/aws_ml_ready.csv"

df = pd.read_csv(input_file)

missing_indicator_columns = [
    column
    for column in df.columns
    if column.endswith("_missing")
]

feature_columns = [
    column
    for column in df.columns
    if column not in missing_indicator_columns
]

print("Rows:", len(df))
print("Input features:", len(df.columns))

print("\nMissing indicators:", len(missing_indicator_columns))
print("Continuous features:", len(feature_columns))

# Replace infinite values with NaN
df[feature_columns] = df[feature_columns].replace(
    [np.inf, -np.inf],
    np.nan
)

missing_before = df[feature_columns].isna().sum()

print("\nMissing values before imputation:")
print(
    missing_before[missing_before > 0]
    .sort_values(ascending=False)
    .to_string()
)

# Median imputation
for column in feature_columns:

    if df[column].isna().any():

        median = df[column].median()

        df[column] = df[column].fillna(median)

# Verify
remaining_missing = df.isna().sum().sum()

remaining_infinite = np.isinf(
    df[feature_columns].to_numpy()
).sum()

print("\nMissing values after imputation:")
print(remaining_missing)

print("\nInfinite values after imputation:")
print(remaining_infinite)

print("\nFinal shape:")
print(df.shape)

print("\nFinal feature list:")

for i, column in enumerate(df.columns, start=1):
    print(f"{i:3}. {column}")

df.to_csv(output_file, index=False)

print("\nSaved:", output_file)