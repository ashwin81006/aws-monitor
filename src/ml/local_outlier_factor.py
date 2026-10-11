import os
import time
import json
import joblib
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor

# ==============================================================================
# LOCAL OUTLIER FACTOR (LOF) MODEL
# ==============================================================================
# Density-based unsupervised anomaly detection. Measures local density deviation
# of an observation with respect to its k-nearest neighbors. Points with lower
# density than neighbors are identified as outliers.
# Must use RobustScaler-transformed features and novelty=True for unseen test scoring.
# ==============================================================================

train_file = "data/processed/aws_train_scaled.csv"
test_file = "data/processed/aws_test_scaled.csv"
features_file = "data/processed/aws_features.csv"

model_file = "models/lof_model.pkl"
results_file = "data/processed/aws_lof_results.csv"
meta_file = "models/training_meta.json"

train = pd.read_csv(train_file)
test = pd.read_csv(test_file)
features = pd.read_csv(features_file)

print("Training shape:", train.shape)
print("Testing shape :", test.shape)

# Novelty=True enables predict() and decision_function() on unseen data
model = LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.01,
    novelty=True,
    n_jobs=-1
)

print("\nTraining Local Outlier Factor (novelty=True)...")
t0 = time.perf_counter()
model.fit(train.values)
fit_time_sec = time.perf_counter() - t0
print(f"Training complete in {fit_time_sec:.4f} seconds.")

# Predictions on uncorrupted test split
test_scores = model.decision_function(test.values)
test_predictions = model.predict(test.values)

results = pd.DataFrame({
    "anomaly_score": test_scores,
    "anomaly_flag": (test_predictions == -1).astype(int)
})

# Attach timestamps from the test window
test_start_index = len(train)
test_timestamps = features.iloc[test_start_index:]["timestamp"].reset_index(drop=True)
results.insert(0, "timestamp", test_timestamps)

print(f"\nTest observations : {len(results)}")
print(f"Anomalies flagged : {results['anomaly_flag'].sum()}")
print(f"Anomaly percentage: {results['anomaly_flag'].mean() * 100:.2f}%")

os.makedirs("models", exist_ok=True)
joblib.dump(model, model_file)
results.to_csv(results_file, index=False)

# Record training meta
meta = {}
if os.path.exists(meta_file):
    try:
        with open(meta_file, "r") as f:
            meta = json.load(f)
    except Exception:
        meta = {}
meta["Local Outlier Factor"] = {
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
