import pandas as pd
import numpy as np

input_file = "data/processed/aws_ml_ready.csv"

df = pd.read_csv(input_file)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nMissing values:", df.isna().sum().sum())

print(
    "Infinite values:",
    np.isinf(df.to_numpy()).sum()
)

print("\nData types:")
print(df.dtypes.value_counts())

print("\nFirst 5 rows:")
print(df.head())

print("\nShape:")
print(df.shape)