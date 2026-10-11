"""
Model Training Module for AWS Anomaly Detection.
Trains Isolation Forest (primary detector), One-Class SVM (boundary baseline),
and Local Outlier Factor (density baseline) using chronological 70/30 split.

Zero intermediate CSV writes - completely in-memory.
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor

# Ensure project root in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.preprocess import load_raw_dataset, preprocess_data
from src.features.feature_engineering import extract_features, FEATURE_COLUMNS

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_models():
    print("=" * 65)
    print(" AWS ANOMALY DETECTION: MODEL TRAINING (IN-MEMORY)")
    print("=" * 65)

    # 1. Load data and extract 13 domain features
    print("1. Loading Tamil Nadu ISRO dataset and extracting features...")
    raw_df = load_raw_dataset()
    _, clean_df = preprocess_data(raw_df)
    features_df = extract_features(clean_df)
    X = features_df[FEATURE_COLUMNS].copy()

    total_rows = len(X)
    print(f"   Loaded {total_rows:,} total observations.")

    # 2. Chronological 70% / 30% train/test split (no future look-ahead)
    split_idx = int(total_rows * 0.70)
    X_train = X.iloc[:split_idx].copy()
    X_test = X.iloc[split_idx:].copy()

    print(f"2. Chronological Split:")
    print(f"   Train split (70%): {len(X_train):,} rows")
    print(f"   Test split  (30%): {len(X_test):,} rows")

    # 3. Fit RobustScaler on training split only
    print("3. Fitting RobustScaler on training split...")
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4. Train Isolation Forest (Primary Model)
    print("4. Training Isolation Forest (Primary Tree-based Detector)...")
    model_if = IsolationForest(
        n_estimators=100,
        contamination=0.03,
        random_state=42,
        n_jobs=-1
    )
    model_if.fit(X_train_scaled)
    print("   [DONE] Isolation Forest trained successfully.")

    # 5. Train One-Class SVM (Baseline Model)
    print("5. Training One-Class SVM (Boundary-based Baseline)...")
    # Subsample training split for fast, efficient SVM fitting
    svm_sample = X_train_scaled[:5000]
    model_svm = OneClassSVM(
        kernel="rbf",
        gamma="scale",
        nu=0.03
    )
    model_svm.fit(svm_sample)
    print("   [DONE] One-Class SVM trained successfully.")

    # 6. Train Local Outlier Factor (Baseline Model)
    print("6. Training Local Outlier Factor (Density-based Baseline)...")
    lof_sample = X_train_scaled[:5000]
    model_lof = LocalOutlierFactor(
        n_neighbors=20,
        contamination=0.03,
        novelty=True
    )
    model_lof.fit(lof_sample)
    print("   [DONE] Local Outlier Factor trained successfully.")

    # 7. Save production model artifacts
    print("\n7. Saving model artifacts to models/ directory...")
    pickle.dump(model_if, open(os.path.join(MODELS_DIR, "isolation_forest.pkl"), "wb"))
    pickle.dump(model_svm, open(os.path.join(MODELS_DIR, "one_class_svm.pkl"), "wb"))
    pickle.dump(model_lof, open(os.path.join(MODELS_DIR, "lof.pkl"), "wb"))
    pickle.dump(scaler, open(os.path.join(MODELS_DIR, "scaler.pkl"), "wb"))

    print("   Saved models/isolation_forest.pkl")
    print("   Saved models/one_class_svm.pkl")
    print("   Saved models/lof.pkl")
    print("   Saved models/scaler.pkl")
    print("=" * 65)
    print(" All models trained and saved cleanly. Ready for testing!")
    print("=" * 65)

    return model_if, model_svm, model_lof, scaler, X_test, X_test_scaled


if __name__ == "__main__":
    train_models()
