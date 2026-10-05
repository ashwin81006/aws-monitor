import pandas as pd

input_file = "data/raw/aws_dataset.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["DATE(IST)"] + " " + df["TIME(IST)"],
    format="mixed"
)

df["month"] = df["timestamp"].dt.to_period("M")

coverage = df.groupby("month").size()

print("Observations per month:")
print(coverage.to_string())

print("\nMonths with fewer than 100 observations:")
print(coverage[coverage < 100].to_string())

print("\nTotal months:", len(coverage))