import pandas as pd

input_file = "data/raw/aws_dataset.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["DATE(IST)"] + " " + df["TIME(IST)"],
    format="mixed"
)

df = df.sort_values("timestamp").reset_index(drop=True)

rain = "RAINFALL(mm)"

print("=== RAINFALL VALUE COUNTS ===")
print(df[rain].value_counts(dropna=False).head(30))

print("\n=== RAINFALL > 100 ===")

mask = df[rain] > 100

print(
    df.loc[
        mask,
        ["timestamp", rain]
    ].head(50).to_string(index=False)
)

print("\n=== RAINFALL CHANGES ===")

df["rain_change"] = df[rain].diff()

mask = (
    (df[rain] > 100) |
    (df["rain_change"].abs() > 100)
)

print(
    df.loc[
        mask,
        ["timestamp", rain, "rain_change"]
    ].head(100).to_string(index=False)
)

print("\n=== VALUES AROUND 2016-09-05 ===")

mask = (
    (df["timestamp"] >= "2016-09-05 12:00:00") &
    (df["timestamp"] <= "2016-09-06 12:00:00")
)

print(
    df.loc[
        mask,
        ["timestamp", rain]
    ].to_string(index=False)
)