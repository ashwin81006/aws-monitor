import pandas as pd

input_file = "data/processed/aws_ml_features.csv"

train_file = "data/processed/aws_train_raw.csv"
test_file = "data/processed/aws_test_raw.csv"


df = pd.read_csv(input_file)

split_index = int(len(df) * 0.70)

train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()


print("Total rows:", len(df))
print("Training rows:", len(train))
print("Testing rows:", len(test))

print(
    "\nTraining percentage:",
    len(train) / len(df) * 100
)

print(
    "Testing percentage:",
    len(test) / len(df) * 100
)


train.to_csv(
    train_file,
    index=False
)

test.to_csv(
    test_file,
    index=False
)


print("\nSaved:")
print(train_file)
print(test_file)