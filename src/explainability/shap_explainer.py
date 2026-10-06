import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap


# ==============================================================================
# TELEMETRY ANOMALY EXPLAINABILITY ENGINE (SHAP TreeExplainer)
# ==============================================================================
# Provides transparent, mathematically rigorous explanations for Isolation Forest
# unsupervised anomaly detections.
#
# Capabilities:
#   1. Local Attribution: Exact Shapley values attributing which specific sensors,
#      rates of change, spreads, or rolling metrics drove an observation into the
#      anomalous region.
#   2. Global Feature Importance: Mean absolute SHAP values across the entire
#      anomalous cohort to identify systemic drivers.
#   3. Event-Level Diagnostics: Enriches fused anomaly events with top contributing
#      features, raw values, and human-readable natural language explanations.
#   4. High-Resolution Visualizations: Global importance bars, summary beeswarm,
#      and single-event waterfall plots saved to reports/figures/.
# ==============================================================================

# Input paths
MODEL_PATH = "models/isolation_forest.pkl"
SCALER_PATH = "models/scaler.pkl"
FEATURE_COLS_PATH = "models/ml_feature_columns.json"

TEST_SCALED_PATH = "data/processed/aws_test_scaled.csv"
FEATURES_PATH = "data/processed/aws_features.csv"
EVIDENCE_MATRIX_PATH = "data/processed/aws_evidence_matrix.csv"
EVENT_FUSION_PATH = "data/processed/aws_event_fusion.csv"

# Output paths
REPORTS_DIR = "reports/figures"
GLOBAL_IMPORTANCE_CSV = "data/processed/aws_shap_global_importance.csv"
EVENT_EXPLANATIONS_CSV = "data/processed/aws_event_explanations.csv"
EXPLANATIONS_SUMMARY_JSON = "data/processed/aws_event_explanations_summary.json"

GLOBAL_BAR_PNG = os.path.join(REPORTS_DIR, "shap_global_importance.png")
BEESWARM_PNG = os.path.join(REPORTS_DIR, "shap_summary_plot.png")
WATERFALL_PNG = os.path.join(REPORTS_DIR, "shap_event_waterfall.png")


class TelemetryShapExplainer:
    """
    Production SHAP Explainer for Automatic Weather Station anomaly detection models.
    """

    def __init__(
        self,
        model_path=MODEL_PATH,
        scaler_path=SCALER_PATH,
        feature_cols_path=FEATURE_COLS_PATH
    ):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        if not os.path.exists(feature_cols_path):
            raise FileNotFoundError(f"Feature columns not found: {feature_cols_path}")

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

        with open(feature_cols_path, "r") as f:
            self.feature_names = json.load(f)

        # Initialize TreeExplainer (exact, fast polynomial-time evaluation)
        self.explainer = shap.TreeExplainer(self.model)
        self.expected_value = float(
            self.explainer.expected_value[0]
            if isinstance(self.explainer.expected_value, (list, np.ndarray))
            else self.explainer.expected_value
        )

    def compute_anomaly_contributions(self, X_scaled):
        """
        Computes SHAP values and inverts sign so that positive values represent
        positive contribution towards isolation/anomalousness.
        """
        # Isolation Forest TreeExplainer outputs path lengths: shorter = more anomalous
        shap_vals = self.explainer.shap_values(X_scaled)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
        # Invert: shorter path length -> positive anomaly contribution
        return -np.array(shap_vals)

    def explain_observation(self, row_scaled, row_raw=None, top_k=5):
        """
        Explains a single observation vector.
        Returns top-k contributing features, their values, and a natural language summary.
        """
        if isinstance(row_scaled, pd.Series):
            X = row_scaled.values.reshape(1, -1)
        elif isinstance(row_scaled, pd.DataFrame):
            X = row_scaled.values
        else:
            X = np.array(row_scaled).reshape(1, -1)

        contribs = self.compute_anomaly_contributions(X)[0]
        sorted_indices = np.argsort(contribs)[::-1]

        top_drivers = []
        for idx in sorted_indices[:top_k]:
            feat = self.feature_names[idx]
            c_val = float(contribs[idx])
            s_val = float(X[0, idx])
            r_val = float(row_raw[feat]) if (row_raw is not None and feat in row_raw) else s_val

            top_drivers.append({
                "feature": feat,
                "anomaly_contribution": round(c_val, 4),
                "scaled_value": round(s_val, 4),
                "raw_value": round(r_val, 4)
            })

        # Generate concise natural language explanation
        phrases = []
        for d in top_drivers[:3]:
            f_name = d["feature"].replace("(", " [").replace(")", "]")
            phrases.append(f"{f_name} (val: {d['raw_value']}, SHAP: +{d['anomaly_contribution']:.3f})")

        explanation_text = "Anomaly driven by: " + "; ".join(phrases)
        return {
            "top_drivers": top_drivers,
            "summary_explanation": explanation_text
        }

    def generate_global_importance(
        self,
        X_sample,
        top_k=20,
        output_csv=GLOBAL_IMPORTANCE_CSV,
        output_plot=GLOBAL_BAR_PNG
    ):
        """
        Computes mean absolute SHAP values across an evaluation cohort
        and exports both a ranking CSV and publication-ready bar chart.
        """
        print(f"\n[1/4] Computing global SHAP feature importance ({len(X_sample)} samples)...")
        contribs = self.compute_anomaly_contributions(X_sample)
        mean_abs_shap = np.mean(np.abs(contribs), axis=0)

        importance_df = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": np.round(mean_abs_shap, 5)
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

        importance_df["rank"] = np.arange(1, len(importance_df) + 1)
        importance_df.to_csv(output_csv, index=False)
        print(f"  Saved global importance rankings: {output_csv}")

        # Plot horizontal bar chart
        os.makedirs(os.path.dirname(output_plot), exist_ok=True)
        top_plot_df = importance_df.head(top_k).iloc[::-1]

        plt.figure(figsize=(10, 7), dpi=300)
        bars = plt.barh(
            top_plot_df["feature"],
            top_plot_df["mean_abs_shap"],
            color="#2b5c8f",
            edgecolor="#1a3b5c",
            alpha=0.88,
            height=0.65
        )
        plt.xlabel("Mean Absolute SHAP Contribution (|Δ Path Length|)", fontsize=11, fontweight="bold")
        plt.title(f"Top {top_k} Telemetry Anomaly Drivers (Global SHAP Importance)", fontsize=13, fontweight="bold", pad=12)
        plt.grid(axis="x", linestyle="--", alpha=0.5)

        # Annotate values at bar tips
        for bar in bars:
            width = bar.get_width()
            plt.text(
                width + 0.002,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.3f}",
                ha="left",
                va="center",
                fontsize=8.5,
                color="#333333"
            )

        plt.tight_layout()
        plt.savefig(output_plot)
        plt.close()
        print(f"  Saved global importance plot: {output_plot}")
        return importance_df

    def generate_summary_plot(
        self,
        X_sample,
        output_plot=BEESWARM_PNG,
        max_display=18
    ):
        """
        Generates a SHAP beeswarm / dot plot illustrating how high vs low feature
        values influence anomaly isolation.
        """
        print(f"\n[2/4] Generating SHAP beeswarm summary plot...")
        os.makedirs(os.path.dirname(output_plot), exist_ok=True)

        shap_vals = self.explainer.shap_values(X_sample)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
        # Invert so higher value = higher anomaly likelihood
        anom_shap_vals = -shap_vals

        plt.figure(figsize=(11, 8), dpi=300)
        shap.summary_plot(
            anom_shap_vals,
            X_sample,
            feature_names=self.feature_names,
            max_display=max_display,
            show=False
        )
        plt.title("SHAP Anomaly Contribution Distribution (Feature Value Impact)", fontsize=12, fontweight="bold", pad=10)
        plt.tight_layout()
        plt.savefig(output_plot)
        plt.close()
        print(f"  Saved summary beeswarm plot: {output_plot}")

    def explain_fused_events(
        self,
        events_csv=EVENT_FUSION_PATH,
        evidence_csv=EVIDENCE_MATRIX_PATH,
        features_csv=FEATURES_PATH,
        output_csv=EVENT_EXPLANATIONS_CSV,
        summary_json=EXPLANATIONS_SUMMARY_JSON,
        top_k=5
    ):
        """
        Associates each fused anomaly event with its peak anomalous observation,
        derives top contributing features via SHAP, and creates human-readable
        diagnostic summaries for weather station operators.
        """
        print(f"\n[3/4] Explaining diagnosed anomaly events...")
        if not os.path.exists(events_csv):
            print(f"Warning: Events file not found: {events_csv}")
            return None

        events_df = pd.read_csv(events_csv)
        events_df["start_time"] = pd.to_datetime(events_df["start_time"])
        events_df["end_time"] = pd.to_datetime(events_df["end_time"])

        matrix_df = pd.read_csv(evidence_csv)
        matrix_df["timestamp"] = pd.to_datetime(matrix_df["timestamp"])

        raw_df = pd.read_csv(features_csv) if os.path.exists(features_csv) else None
        if raw_df is not None:
            raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"])

        test_scaled = pd.read_csv(TEST_SCALED_PATH)
        split_idx = len(matrix_df) - len(test_scaled)
        test_timestamps = matrix_df.iloc[split_idx:]["timestamp"].reset_index(drop=True)
        time_to_scaled_idx = {t: idx for idx, t in enumerate(test_timestamps)}

        explanations = []
        for _, ev in events_df.iterrows():
            eid = int(ev["event_id"])
            s_time = ev["start_time"]
            e_time = ev["end_time"]

            # Filter observations within event window
            ev_obs = matrix_df[(matrix_df["timestamp"] >= s_time) & (matrix_df["timestamp"] <= e_time)]
            if len(ev_obs) == 0:
                continue

            # Pick peak anomaly observation (lowest IF score or highest fused score)
            if "anomaly_score" in ev_obs.columns and ev_obs["anomaly_score"].notna().any():
                peak_row = ev_obs.loc[ev_obs["anomaly_score"].idxmin()]
            else:
                peak_row = ev_obs.iloc[0]

            peak_time = peak_row["timestamp"]
            scaled_idx = time_to_scaled_idx.get(peak_time)

            if scaled_idx is not None and scaled_idx < len(test_scaled):
                x_scaled = test_scaled.iloc[[scaled_idx]]
                x_raw = raw_df[raw_df["timestamp"] == peak_time].iloc[0] if raw_df is not None else None
                exp = self.explain_observation(x_scaled, row_raw=x_raw, top_k=top_k)

                driver_strings = [
                    f"{d['feature']} (val: {d['raw_value']}, SHAP: +{d['anomaly_contribution']:.3f})"
                    for d in exp["top_drivers"]
                ]
                top_feature_names = [d["feature"] for d in exp["top_drivers"]]
                primary_feature = top_feature_names[0] if top_feature_names else "UNKNOWN"
            else:
                exp = {"summary_explanation": "ML inference not evaluated for historical pre-test split."}
                driver_strings = []
                primary_feature = "NON_TEST_PERIOD"

            record = {
                "event_id": eid,
                "start_time": str(s_time),
                "end_time": str(e_time),
                "observations": ev["observations"],
                "candidate_class": ev.get("candidate_class", "UNCERTAIN"),
                "severity": ev.get("severity", "LOW"),
                "confidence": ev.get("confidence", 0.5),
                "probable_root_cause": ev.get("probable_root_cause", "UNKNOWN"),
                "target_sensor": ev.get("target_sensor", "MULTI_SENSOR"),
                "peak_anomaly_timestamp": str(peak_time),
                "primary_ml_driver": primary_feature,
                "top_5_ml_drivers": "; ".join(driver_strings),
                "diagnostic_explanation": exp["summary_explanation"]
            }
            explanations.append(record)

        exp_df = pd.DataFrame(explanations)
        exp_df.to_csv(output_csv, index=False)
        print(f"  Saved event explanations: {output_csv} ({len(exp_df)} events explained)")

        # Save summary JSON
        summary_stats = {
            "total_explained_events": len(exp_df),
            "primary_ml_drivers_breakdown": exp_df["primary_ml_driver"].value_counts().head(10).to_dict(),
            "target_sensor_breakdown": exp_df["target_sensor"].value_counts().to_dict(),
            "sample_explanations": exp_df[[
                "event_id", "target_sensor", "candidate_class", "probable_root_cause", "diagnostic_explanation"
            ]].head(5).to_dict(orient="records")
        }
        with open(summary_json, "w") as f:
            json.dump(summary_stats, f, indent=4)
        print(f"  Saved explanations summary JSON: {summary_json}")
        return exp_df

    def generate_event_waterfall_plot(
        self,
        event_id=None,
        events_csv=EVENT_FUSION_PATH,
        evidence_csv=EVIDENCE_MATRIX_PATH,
        features_csv=FEATURES_PATH,
        output_plot=WATERFALL_PNG,
        top_k=10
    ):
        """
        Creates an annotated horizontal bar contribution chart for a specific diagnosed
        anomaly event, highlighting how specific physical features contributed.
        """
        print(f"\n[4/4] Generating event waterfall contribution plot...")
        if not os.path.exists(events_csv) or not os.path.exists(evidence_csv):
            return

        events_df = pd.read_csv(events_csv)
        events_df["start_time"] = pd.to_datetime(events_df["start_time"])
        events_df["end_time"] = pd.to_datetime(events_df["end_time"])

        # Pick event with high confidence and multiple observations if not specified
        if event_id is None:
            # Prefer severe or sensor fault events
            candidates = events_df[
                (events_df["candidate_class"] == "PROBABLE_SENSOR_FAULT") |
                (events_df["candidate_class"] == "STATION_SYSTEM_FAILURE")
            ]
            if len(candidates) > 0:
                event_row = candidates.iloc[len(candidates) // 2]
            else:
                event_row = events_df.iloc[0]
            event_id = int(event_row["event_id"])
        else:
            match = events_df[events_df["event_id"] == event_id]
            if len(match) == 0:
                event_row = events_df.iloc[0]
                event_id = int(event_row["event_id"])
            else:
                event_row = match.iloc[0]

        s_time = event_row["start_time"]
        e_time = event_row["end_time"]
        cand_class = event_row.get("candidate_class", "UNKNOWN")
        root_cause = event_row.get("probable_root_cause", "UNKNOWN")
        target_sensor = event_row.get("target_sensor", "UNKNOWN")

        matrix_df = pd.read_csv(evidence_csv)
        matrix_df["timestamp"] = pd.to_datetime(matrix_df["timestamp"])
        ev_obs = matrix_df[(matrix_df["timestamp"] >= s_time) & (matrix_df["timestamp"] <= e_time)]

        peak_row = ev_obs.loc[ev_obs["anomaly_score"].idxmin()] if ("anomaly_score" in ev_obs and ev_obs["anomaly_score"].notna().any()) else ev_obs.iloc[0]
        peak_time = peak_row["timestamp"]

        test_scaled = pd.read_csv(TEST_SCALED_PATH)
        split_idx = len(matrix_df) - len(test_scaled)
        test_timestamps = matrix_df.iloc[split_idx:]["timestamp"].reset_index(drop=True)
        time_to_idx = {t: idx for idx, t in enumerate(test_timestamps)}
        idx = time_to_idx.get(peak_time, 0)

        x_scaled = test_scaled.iloc[[idx]]
        contribs = self.compute_anomaly_contributions(x_scaled)[0]

        top_indices = np.argsort(contribs)[::-1][:top_k]
        top_features = [self.feature_names[i] for i in top_indices]
        top_contribs = [contribs[i] for i in top_indices]

        # Invert order for top-to-bottom bar chart
        plot_features = top_features[::-1]
        plot_vals = top_contribs[::-1]

        plt.figure(figsize=(10, 6), dpi=300)
        colors = ["#d9534f" if v > 0 else "#5bc0de" for v in plot_vals]
        bars = plt.barh(plot_features, plot_vals, color=colors, height=0.6, edgecolor="#333333", alpha=0.85)

        plt.axvline(0, color="black", linestyle="-", linewidth=0.8)
        plt.xlabel("SHAP Anomaly Contribution (+ pushes towards anomaly)", fontsize=11, fontweight="bold")
        plt.title(
            f"Event #{event_id} Feature Attribution (Peak: {peak_time})\n"
            f"Class: {cand_class} | Cause: {root_cause} | Target: {target_sensor}",
            fontsize=12,
            fontweight="bold",
            pad=10
        )
        plt.grid(axis="x", linestyle="--", alpha=0.5)

        for bar in bars:
            w = bar.get_width()
            offset = 0.005 if w >= 0 else -0.005
            ha = "left" if w >= 0 else "right"
            plt.text(w + offset, bar.get_y() + bar.get_height() / 2, f"{w:+.3f}", va="center", ha=ha, fontsize=9)

        plt.tight_layout()
        os.makedirs(os.path.dirname(output_plot), exist_ok=True)
        plt.savefig(output_plot)
        plt.close()
        print(f"  Saved event waterfall plot: {output_plot} (Event #{event_id})")


def run_explainability():
    """
    Main entry point for running the complete SHAP explainability pipeline.
    """
    print("=" * 65)
    print("    TELEMETRY MODEL EXPLAINABILITY PIPELINE (SHAP)")
    print("=" * 65)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    explainer = TelemetryShapExplainer()
    test_scaled = pd.read_csv(TEST_SCALED_PATH)

    # 1. Representative sample for global explanations (e.g. 500 points)
    sample_size = min(600, len(test_scaled))
    np.random.seed(42)
    sample_indices = np.random.choice(len(test_scaled), size=sample_size, replace=False)
    X_sample = test_scaled.iloc[sample_indices].reset_index(drop=True)

    # 2. Global Importance
    explainer.generate_global_importance(X_sample=X_sample, top_k=20)

    # 3. Summary Beeswarm Plot
    explainer.generate_summary_plot(X_sample=X_sample, max_display=18)

    # 4. Event-level Explanations
    explainer.explain_fused_events()

    # 5. Event Waterfall Plot
    explainer.generate_event_waterfall_plot()

    print("\n" + "=" * 65)
    print("        SHAP EXPLAINABILITY PIPELINE COMPLETED")
    print("=" * 65)


if __name__ == "__main__":
    run_explainability()
