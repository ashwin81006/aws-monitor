import os
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

train_file = "data/processed/aws_train_ready.csv"
test_file = "data/processed/aws_test_ready.csv"
features_file = "data/processed/aws_features.csv"

model_file = "models/isolation_forest.pkl"
results_file = "data/processed/aws_if_results.csv"


train = pd.read_csv(train_file)
test = pd.read_csv(test_file)
features = pd.read_csv(features_file)


print("Training shape:", train.shape)
print("Testing shape:", test.shape)


model = IsolationForest(
    n_estimators=100,
    contamination=0.01,
    random_state=42
)


print("\nTraining Isolation Forest...")

model.fit(train)


print("Training complete.")


# Generate predictions for the future test period
test_scores = model.decision_function(test)

test_predictions = model.predict(test)


results = pd.DataFrame({
    "anomaly_score": test_scores,
    "anomaly_flag": (test_predictions == -1).astype(int)
})


# Attach timestamps from the original feature dataset
test_start_index = len(train)

test_timestamps = features.iloc[
    test_start_index:
]["timestamp"].reset_index(drop=True)


results.insert(
    0,
    "timestamp",
    test_timestamps
)


print("\nTest observations:", len(results))

print(
    "Anomalies:",
    results["anomaly_flag"].sum()
)

print(
    "Anomaly percentage:",
    results["anomaly_flag"].mean() * 100
)


print("\nScore statistics:")
print(
    results["anomaly_score"].describe()
)


# Create model directory
os.makedirs(
    "models",
    exist_ok=True
)


# Save trained model
joblib.dump(
    model,
    model_file
)


# Save predictions
results.to_csv(
    results_file,
    index=False
)


print("\nSaved model:")
print(model_file)

print("\nSaved results:")
print(results_file)