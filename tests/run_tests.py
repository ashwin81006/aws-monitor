import sys
import os
import traceback

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tests.test_dataset_schema as t_ds
import tests.test_features as t_feat
import tests.test_feature_equivalence as t_equiv
import tests.test_models as t_mod
import tests.test_detection_rules as t_rules
import tests.test_fusion as t_fus
import tests.test_known_value_fusion as t_kv_fus
import tests.test_event_metric_math as t_event_math
import tests.test_upload_validation as t_upload
import tests.test_api_health_states as t_health_states
import tests.test_api_endpoints as t_api

test_modules = [
    ("Dataset Schema Tests", t_ds),
    ("Feature Specification Tests", t_feat),
    ("Causal Feature Equivalence & Zero-Leakage Tests", t_equiv),
    ("Model & ML Inference Tests", t_mod),
    ("Physics & Bayesian Detection Rule Tests", t_rules),
    ("Evidence Matrix & Fusion Tests", t_fus),
    ("Analytical Noisy-OR & Physical Scenario Tests", t_kv_fus),
    ("Event-Level Overlap Metric Validation Tests", t_event_math),
    ("Upload Schema Validation & Security Rejection Tests", t_upload),
    ("Health State & Degradation Transparency Tests", t_health_states),
    ("FastAPI REST Endpoint Tests", t_api),
]

total_passed = 0
total_failed = 0

print("=" * 70)
print("             AWS MONITOR AUTOMATED TEST RUNNER")
print("=" * 70)

for suite_name, module in test_modules:
    print(f"\n>> Running Suite: {suite_name}")

    for attr_name in dir(module):
        if attr_name.startswith("test_") and callable(getattr(module, attr_name)):
            fn = getattr(module, attr_name)
            try:
                fn()
                print(f"  [PASS] {attr_name}")
                total_passed += 1
            except Exception as e:
                print(f"  [FAIL] {attr_name}: {e}")
                traceback.print_exc()
                total_failed += 1

print("\n" + "=" * 70)
print(f"TEST SUMMARY: {total_passed} Passed | {total_failed} Failed | Total: {total_passed + total_failed}")
print("=" * 70)

if total_failed > 0:
    sys.exit(1)
else:
    sys.exit(0)
