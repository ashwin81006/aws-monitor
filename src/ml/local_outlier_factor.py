import os
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
# Pass numpy array to avoid feature-name validation warnings
model.fit(train.values)
print("Training complete.")

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

print("\nScore statistics:")
print(results["anomaly_score"].describe())

# Save artifacts
os.makedirs("models", exist_ok=True)
joblib.dump(model, model_file)
results.to_csv(results_file, index=False)

print(f"\nSaved model   : {model_file}")
print(f"Saved results : {results_file}")
