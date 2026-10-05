import pandas as pd
import numpy as np

train_file = "data/processed/aws_train_raw.csv"
test_file = "data/processed/aws_test_raw.csv"

train_output = "data/processed/aws_train_ready.csv"
test_output = "data/processed/aws_test_ready.csv"


train = pd.read_csv(train_file)
test = pd.read_csv(test_file)


print("Training shape:", train.shape)
print("Testing shape:", test.shape)


# Missing indicators are already meaningful binary features.
missing_columns = [
    column
    for column in train.columns
    if column.endswith("_missing")
]


continuous_columns = [
    column
    for column in train.columns
    if column not in missing_columns
]


print(
    "\nMissing indicator features:",
    len(missing_columns)
)

print(
    "Continuous features:",
    len(continuous_columns)
)


# Replace infinite values with NaN.
train[continuous_columns] = (
    train[continuous_columns]
    .replace([np.inf, -np.inf], np.nan)
)

test[continuous_columns] = (
    test[continuous_columns]
    .replace([np.inf, -np.inf], np.nan)
)


# Learn medians ONLY from training data.
train_medians = train[
    continuous_columns
].median()


# Check whether any feature cannot get a training median.
missing_medians = train_medians[
    train_medians.isna()
]


if len(missing_medians) > 0:

    print(
        "\nFeatures with no training median:"
    )

    print(
        missing_medians.index.tolist()
    )

    raise ValueError(
        "Cannot safely impute these features."
    )


# Apply training medians to both train and test.
train[continuous_columns] = (
    train[continuous_columns]
    .fillna(train_medians)
)

test[continuous_columns] = (
    test[continuous_columns]
    .fillna(train_medians)
)


# Verify
train_missing = train.isna().sum().sum()
test_missing = test.isna().sum().sum()

train_infinite = np.isinf(
    train.to_numpy()
).sum()

test_infinite = np.isinf(
    test.to_numpy()
).sum()


print("\nAfter imputation:")

print(
    "Training missing values:",
    train_missing
)

print(
    "Testing missing values:",
    test_missing
)

print(
    "Training infinite values:",
    train_infinite
)

print(
    "Testing infinite values:",
    test_infinite
)


if (
    train_missing > 0
    or test_missing > 0
    or train_infinite > 0
    or test_infinite > 0
):

    raise ValueError(
        "ML data still contains invalid values."
    )


train.to_csv(
    train_output,
    index=False
)

test.to_csv(
    test_output,
    index=False
)


print("\nSaved:")
print(train_output)
print(test_output)