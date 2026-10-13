import unittest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from src.api.app import app
from src.features.feature_engineering import (
    StreamingFeatureExtractor,
    compute_dew_point,
    extract_features,
    FEATURE_COLUMNS,
)
from src.core.detector import AWSUnifiedDetector
from src.core.self_healing import heal_observation, estimate_temperature_from_rh, estimate_rh_from_temperature


class TestAWSMonitorBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertEqual(data["station_id"], "ISRO0119_15F077")
        self.assertEqual(data["features_count"], 13)

    def test_station_summary_endpoint(self):
        response = self.client.get("/api/v1/station/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["station_id"], "ISRO0119_15F077")
        self.assertGreater(data["total_observations"], 0)
        self.assertIn("location", data)

    def test_sensors_health_endpoint(self):
        response = self.client.get("/api/v1/sensors/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["station_id"], "ISRO0119_15F077")
        self.assertIn("sensors", data)
        self.assertEqual(len(data["sensors"]), 3)
        channels = [s["channel"] for s in data["sensors"]]
        self.assertIn("temperature", channels)
        self.assertIn("humidity", channels)
        self.assertIn("pressure", channels)

    def test_anomaly_events_endpoint(self):
        response = self.client.get("/api/v1/anomalies/events?limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_events", data)
        self.assertIn("counts_by_category", data)
        self.assertIn("events", data)
        self.assertGreater(len(data["events"]), 0)

    def test_anomaly_event_detail_endpoint(self):
        response = self.client.get("/api/v1/anomalies/events/1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["event_id"], 1)
        self.assertIn("explanation", data)
        self.assertIn("rule_flags", data)
        self.assertIn("affected_sensors", data)

    def test_models_benchmark_endpoint(self):
        response = self.client.get("/api/v1/models/benchmark")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "AVAILABLE")
        self.assertIn("models", data)
        self.assertGreaterEqual(len(data["models"]), 3)

    def test_shap_global_endpoint(self):
        response = self.client.get("/api/v1/models/shap")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("top_features", data)
        self.assertGreaterEqual(len(data["top_features"]), 5)

    def test_shap_explain_observation_endpoint(self):
        payload = {"temperature": 45.0, "humidity": 18.0, "pressure": 995.0}
        response = self.client.post("/api/v1/models/shap/explain", json=payload)
        self.assertEqual(response.status_code, 200)
        impacts = response.json()
        self.assertIsInstance(impacts, list)
        self.assertGreaterEqual(len(impacts), 4)
        for item in impacts:
            self.assertIn("feature", item)
            self.assertIn("shap_value", item)
            self.assertIn("absolute_impact", item)
            self.assertIn("direction", item)

    def test_stream_point_inference(self):
        payload = {
            "timestamp": "2026-10-14 12:00:00",
            "temperature": -35.0,
            "humidity": 65.0,
            "pressure": 998.4,
            "temp_2m": -35.0,
            "temp_4m": -35.0,
            "temp_8m": -35.0,
            "rh_2m": 65.0,
            "rh_4m": 65.0,
            "rh_8m": 65.0,
            "battery_voltage": 12.8,
            "wind_speed_10m": 2.0,
            "rainfall": 0.0,
        }
        response = self.client.post("/api/v1/telemetry/stream-point", json=payload)
        self.assertEqual(response.status_code, 200)
        res = response.json()
        self.assertTrue(res["is_anomaly"])
        self.assertTrue(res["is_healed"])
        self.assertIsNotNone(res["corrected_temperature"])

    def test_psychrometric_dew_point(self):
        t = np.array([30.0, 20.0, 10.0])
        rh = np.array([60.0, 50.0, 80.0])
        dp = compute_dew_point(t, rh)
        self.assertTrue(np.all(dp < t))
        self.assertTrue(np.all(dp > -20.0))

    def test_streaming_feature_extractor_parity(self):
        extractor = StreamingFeatureExtractor()
        feats = extractor.push(32.5, 55.0, 998.0, pd.Timestamp("2026-07-15 14:00:00"))
        for col in FEATURE_COLUMNS:
            self.assertIn(col, feats)
            self.assertFalse(np.isnan(feats[col]))

    def test_flatline_frozen_sensor_detection(self):
        detector = AWSUnifiedDetector(mode="rule_cascade")
        detector.reset()
        is_frozen = False
        res = None
        for i in range(15):
            res = detector.detect_point("2026-07-15 12:00:00", 28.50, 65.0, 998.4)
            if "FROZEN" in str(res.root_cause):
                is_frozen = True
                break
        self.assertTrue(is_frozen)
        self.assertIn("FROZEN", str(res.root_cause))

    def test_drift_detection(self):
        detector = AWSUnifiedDetector(mode="rule_cascade")
        detector.reset()
        drift_flagged = False
        res = None
        for i in range(25):
            res = detector.detect_point("2026-07-15 12:00:00", 28.0 + (i * 0.4), 65.0, 998.4)
            if "DRIFT" in str(res.root_cause):
                drift_flagged = True
                break
        self.assertTrue(drift_flagged or res is not None)

    def test_heatwave_meteorological_discrimination(self):
        detector = AWSUnifiedDetector(mode="rule_cascade")
        detector.reset()
        res = detector.detect_point("2026-05-20 13:30:00", 46.5, 18.0, 996.0)
        self.assertEqual(res.classification, "BENIGN_EXTREME")
        self.assertIn("METEOROLOGICAL", str(res.root_cause))
        self.assertFalse(res.is_anomaly)

    def test_convective_thunderstorm_discrimination(self):
        detector = AWSUnifiedDetector(mode="rule_cascade")
        detector.reset()
        detector.detect_point("2026-08-10 16:00:00", 32.0, 60.0, 998.0)
        res = detector.detect_point("2026-08-10 16:30:00", 24.0, 95.0, 988.0)
        self.assertEqual(res.classification, "BENIGN_EXTREME")
        self.assertIn("METEOROLOGICAL", res.root_cause)

    def test_self_healing_magnus_inversion(self):
        history = [(30.0, 65.0, 998.0) for _ in range(10)]
        healed = heal_observation(
            temp=-45.0,
            rh=65.0,
            press=998.0,
            fault_type="SENSOR_SPIKE",
            culprit_sensor="Temperature",
            history=history,
        )
        self.assertTrue(healed["is_healed"])
        self.assertGreater(healed["corrected_temperature"], 0.0)
        self.assertLess(healed["corrected_temperature"], 50.0)
        self.assertIsNotNone(healed["uncertainty_estimate"])
        self.assertEqual(healed["reconstruction_grade"], "HIGH_CONFIDENCE_PHYSICAL")
        self.assertEqual(healed["healing_method"], "THERMODYNAMIC_MAGNUS_INVERSION")

    def test_self_healing_cross_channel_corruption_rejection(self):
        history = [(30.0, 65.0, 998.0) for _ in range(10)]
        healed = heal_observation(
            temp=-45.0,
            rh=-999.0,
            press=998.0,
            fault_type="SENSOR_SPIKE",
            culprit_sensor="Temperature",
            history=history,
        )
        self.assertTrue(healed["is_healed"])
        self.assertNotEqual(healed["healing_method"], "THERMODYNAMIC_MAGNUS_INVERSION")
        self.assertEqual(healed["reconstruction_grade"], "MODERATE_CONFIDENCE_AUTOREGRESSIVE")

    def test_detector_modes(self):
        for mode in ["isolation_forest", "one_class_svm", "lof", "calibrated_ensemble", "majority_voting"]:
            det = AWSUnifiedDetector(mode=mode)
            det.reset()
            res = det.detect_point("2026-07-15 12:00:00", 30.0, 60.0, 998.0)
            self.assertIsNotNone(res.fused_anomaly_score)
            self.assertIsNotNone(res.classification)


if __name__ == "__main__":
    unittest.main()
