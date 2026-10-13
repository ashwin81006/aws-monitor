import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.preprocess import load_raw_dataset, preprocess_data
from src.features.feature_engineering import extract_features, FEATURE_COLUMNS

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_models():
    raw_df = load_raw_dataset()
    _, clean_df = preprocess_data(raw_df)
    features_df = extract_features(clean_df)
    X = features_df[FEATURE_COLUMNS].copy()

    total_rows = len(X)
    split_idx = int(total_rows * 0.70)
    X_train = X.iloc[:split_idx].copy()
    X_test = X.iloc[split_idx:].copy()

    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model_if = IsolationForest(
        n_estimators=100,
        contamination=0.03,
        random_state=42,
        n_jobs=-1
    )
    model_if.fit(X_train_scaled)

    svm_sample = X_train_scaled[:5000]
    model_svm = OneClassSVM(
        kernel="rbf",
        gamma="scale",
        nu=0.03
    )
    model_svm.fit(svm_sample)

    lof_sample = X_train_scaled[:5000]
    model_lof = LocalOutlierFactor(
        n_neighbors=20,
        contamination=0.03,
        novelty=True
    )
    model_lof.fit(lof_sample)

    pickle.dump(model_if, open(os.path.join(MODELS_DIR, "isolation_forest.pkl"), "wb"))
    pickle.dump(model_svm, open(os.path.join(MODELS_DIR, "one_class_svm.pkl"), "wb"))
    pickle.dump(model_lof, open(os.path.join(MODELS_DIR, "lof.pkl"), "wb"))
    pickle.dump(scaler, open(os.path.join(MODELS_DIR, "scaler.pkl"), "wb"))

    return model_if, model_svm, model_lof, scaler, X_test, X_test_scaled


if __name__ == "__main__":
    train_models()
