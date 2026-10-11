import os
import time
import json
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

train_file = "data/processed/aws_train_scaled.csv"
test_file = "data/processed/aws_test_scaled.csv"
features_file = "data/processed/aws_features.csv"

model_file = "models/isolation_forest.pkl"
results_file = "data/processed/aws_if_results.csv"
meta_file = "models/training_meta.json"

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
t0 = time.perf_counter()
model.fit(train)
fit_time_sec = time.perf_counter() - t0
print(f"Training complete in {fit_time_sec:.4f} seconds.")

# Generate predictions for the future test period
test_scores = model.decision_function(test)
test_predictions = model.predict(test)

results = pd.DataFrame({
    "anomaly_score": test_scores,
    "anomaly_flag": (test_predictions == -1).astype(int)
})

# Attach timestamps from the original feature dataset
test_start_index = len(train)
test_timestamps = features.iloc[test_start_index:]["timestamp"].reset_index(drop=True)
results.insert(0, "timestamp", test_timestamps)

print("\nTest observations:", len(results))
print("Anomalies:", results["anomaly_flag"].sum())
print("Anomaly percentage:", results["anomaly_flag"].mean() * 100)

os.makedirs("models", exist_ok=True)
joblib.dump(model, model_file)
results.to_csv(results_file, index=False)

# Update training meta json
meta = {}
if os.path.exists(meta_file):
    try:
        with open(meta_file, "r") as f:
            meta = json.load(f)
    except Exception:
        meta = {}
meta["Isolation Forest"] = {
    "fit_time_sec": round(fit_time_sec, 4),
    "n_samples": len(train),
    "n_features": train.shape[1],
    "timestamp": pd.Timestamp.now().isoformat()
}
with open(meta_file, "w") as f:
    json.dump(meta, f, indent=2)

print("\nSaved model:", model_file)
print("Saved results:", results_file)
print("Recorded training meta in:", meta_file)