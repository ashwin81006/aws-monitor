import os
import pandas as pd
import numpy as np


INPUT_CLEAN = "data/processed/aws_clean.csv"
OUTPUT_FAULTY = "data/processed/aws_faulty_clean.csv"
OUTPUT_LABELS = "data/processed/aws_fault_labels.csv"
OUTPUT_EVENTS = "data/processed/aws_injected_events.csv"


def inject_synthetic_faults():
    print("=" * 60)
    print("       CONTROLLED SYNTHETIC FAULT INJECTION")
    print("=" * 60)

    df = pd.read_csv(INPUT_CLEAN)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Establish train/test boundary
    split_index = int(len(df) * 0.70)
    print(f"Total rows: {len(df)}")
    print(f"Test partition starts at index: {split_index} ({df.loc[split_index, 'timestamp']})")

    # Create ground truth tracking columns
    df["is_fault"] = 0
    df["fault_type"] = "NORMAL"
    df["fault_id"] = ""
    df["target_sensor"] = ""
    df["is_extreme_weather"] = 0

    injected_events_meta = []

    # ----------------------------------------------------
    # Fault 1: Sudden Temperature Spike (+10.0°C at 2m height)
    # ----------------------------------------------------
    f1_time = pd.to_datetime("2017-01-09 14:00:00")
    f1_idx = df[df["timestamp"] == f1_time].index
    if len(f1_idx) > 0:
        idx = f1_idx[0]
        col = "AIR_TEMPERATURE1(°C at 2m height)"
        df.loc[idx, col] += 10.0
        df.loc[idx, "is_fault"] = 1
        df.loc[idx, "fault_type"] = "SPIKE"
        df.loc[idx, "fault_id"] = "FAULT_SPIKE_TEMP"
        df.loc[idx, "target_sensor"] = "AIR_TEMPERATURE1"
        injected_events_meta.append({
            "fault_id": "FAULT_SPIKE_TEMP",
            "fault_type": "SPIKE",
            "target_sensor": "AIR_TEMPERATURE1",
            "start_time": str(f1_time),
            "end_time": str(f1_time),
            "duration_minutes": 30,
            "observations": 1,
            "expected_class": "PROBABLE_SENSOR_FAULT",
            "expected_root_cause": "SENSOR_SPIKE",
            "expected_severity": "HIGH"
        })
        print(f"[Injected] FAULT_SPIKE_TEMP at {f1_time}: +10.0°C on {col}")

    # ----------------------------------------------------
    # Fault 2: Sudden Relative Humidity Drop (-35.0% at 4m height)
    # ----------------------------------------------------
    f2_time = pd.to_datetime("2017-03-07 14:00:00")
    f2_idx = df[df["timestamp"] == f2_time].index
    if len(f2_idx) > 0:
        idx = f2_idx[0]
        col = "RELATIVE_HUMIDITY2(% at 4m height)"
        df.loc[idx, col] = max(0.0, df.loc[idx, col] - 35.0)
        df.loc[idx, "is_fault"] = 1
        df.loc[idx, "fault_type"] = "SPIKE"
        df.loc[idx, "fault_id"] = "FAULT_SPIKE_RH"
        df.loc[idx, "target_sensor"] = "RELATIVE_HUMIDITY2"
        injected_events_meta.append({
            "fault_id": "FAULT_SPIKE_RH",
            "fault_type": "SPIKE",
            "target_sensor": "RELATIVE_HUMIDITY2",
            "start_time": str(f2_time),
            "end_time": str(f2_time),
            "duration_minutes": 30,
            "observations": 1,
            "expected_class": "PROBABLE_SENSOR_FAULT",
            "expected_root_cause": "SENSOR_SPIKE",
            "expected_severity": "HIGH"
        })
        print(f"[Injected] FAULT_SPIKE_RH at {f2_time}: -35.0% on {col}")

    # ----------------------------------------------------
    # Fault 3: Frozen/Stuck Temperature Sensor (4m height for 6 hours)
    # ----------------------------------------------------
    f3_start = pd.to_datetime("2017-03-17 04:00:00")
    f3_end = pd.to_datetime("2017-03-17 10:00:00")
    f3_indices = df[(df["timestamp"] >= f3_start) & (df["timestamp"] <= f3_end)].index
    if len(f3_indices) > 0:
        col = "AIR_TEMPERATURE2(°C at 4m height)"
        frozen_val = df.loc[f3_indices[0], col]
        for idx in f3_indices:
            df.loc[idx, col] = frozen_val
            df.loc[idx, "is_fault"] = 1
            df.loc[idx, "fault_type"] = "FROZEN_SENSOR"
            df.loc[idx, "fault_id"] = "FAULT_FROZEN_TEMP"
            df.loc[idx, "target_sensor"] = "AIR_TEMPERATURE2"
        injected_events_meta.append({
            "fault_id": "FAULT_FROZEN_TEMP",
            "fault_type": "FROZEN_SENSOR",
            "target_sensor": "AIR_TEMPERATURE2",
            "start_time": str(f3_start),
            "end_time": str(f3_end),
            "duration_minutes": int((f3_end - f3_start).total_seconds() / 60),
            "observations": len(f3_indices),
            "expected_class": "PROBABLE_SENSOR_FAULT",
            "expected_root_cause": "FROZEN_SENSOR",
            "expected_severity": "HIGH"
        })
        print(f"[Injected] FAULT_FROZEN_TEMP from {f3_start} to {f3_end}: stuck at {frozen_val:.2f}°C ({len(f3_indices)} observations)")

    # ----------------------------------------------------
    # Fault 4: Gradual Sensor Calibration Drift (+0.45°C/obs over 8 hours)
    # ----------------------------------------------------
    f4_start = pd.to_datetime("2017-03-22 00:00:00")
    f4_end = pd.to_datetime("2017-03-22 08:00:00")
    f4_indices = df[(df["timestamp"] >= f4_start) & (df["timestamp"] <= f4_end)].index
    if len(f4_indices) > 0:
        col = "AIR_TEMPERATURE1(°C at 2m height)"
        for step, idx in enumerate(f4_indices, start=1):
            drift_val = 0.45 * step
            df.loc[idx, col] += drift_val
            df.loc[idx, "is_fault"] = 1
            df.loc[idx, "fault_type"] = "DRIFT"
            df.loc[idx, "fault_id"] = "FAULT_DRIFT_TEMP"
            df.loc[idx, "target_sensor"] = "AIR_TEMPERATURE1"
        injected_events_meta.append({
            "fault_id": "FAULT_DRIFT_TEMP",
            "fault_type": "DRIFT",
            "target_sensor": "AIR_TEMPERATURE1",
            "start_time": str(f4_start),
            "end_time": str(f4_end),
            "duration_minutes": int((f4_end - f4_start).total_seconds() / 60),
            "observations": len(f4_indices),
            "expected_class": "PROBABLE_SENSOR_FAULT",
            "expected_root_cause": "CALIBRATION_DRIFT_OR_BIAS",
            "expected_severity": "HIGH"
        })
        print(f"[Injected] FAULT_DRIFT_TEMP from {f4_start} to {f4_end}: ramped up to +{0.45 * len(f4_indices):.2f}°C ({len(f4_indices)} observations)")

    # ----------------------------------------------------
    # Fault 5: Power / Station Collapse (0V battery, 0 pressure, 0 core)
    # ----------------------------------------------------
    f5_start = pd.to_datetime("2017-03-11 02:00:00")
    f5_end = pd.to_datetime("2017-03-11 05:00:00")
    f5_indices = df[(df["timestamp"] >= f5_start) & (df["timestamp"] <= f5_end)].index
    if len(f5_indices) > 0:
        temp_cols = [c for c in df.columns if "AIR_TEMPERATURE" in c and not c.endswith("_invalid")]
        rh_cols = [c for c in df.columns if "RELATIVE_HUMIDITY" in c and not c.endswith("_invalid")]
        for idx in f5_indices:
            df.loc[idx, "BATTRY_VOLTAGE(V)"] = 0.0
            df.loc[idx, "ATMOSPHERIC_PRESSURE(mbar) "] = 0.0
            for tc in temp_cols:
                df.loc[idx, tc] = 0.0
            for rc in rh_cols:
                df.loc[idx, rc] = 0.0
            df.loc[idx, "is_fault"] = 1
            df.loc[idx, "fault_type"] = "POWER_FAILURE"
            df.loc[idx, "fault_id"] = "FAULT_POWER_FAILURE"
            df.loc[idx, "target_sensor"] = "STATION"
        injected_events_meta.append({
            "fault_id": "FAULT_POWER_FAILURE",
            "fault_type": "POWER_FAILURE",
            "target_sensor": "STATION",
            "start_time": str(f5_start),
            "end_time": str(f5_end),
            "duration_minutes": int((f5_end - f5_start).total_seconds() / 60),
            "observations": len(f5_indices),
            "expected_class": "STATION_SYSTEM_FAILURE",
            "expected_root_cause": "STATION_OR_POWER_FAILURE",
            "expected_severity": "CRITICAL"
        })
        print(f"[Injected] FAULT_POWER_FAILURE from {f5_start} to {f5_end}: 0V battery & all core 0.0 ({len(f5_indices)} observations)")

    # ----------------------------------------------------
    # Control 6: Benign Weather Extreme (Consensus rapid storm drop across ALL heights)
    # ----------------------------------------------------
    f6_time = pd.to_datetime("2017-04-02 21:00:00")
    f6_idx = df[df["timestamp"] == f6_time].index
    if len(f6_idx) > 0:
        idx = f6_idx[0]
        temp_cols = [c for c in df.columns if "AIR_TEMPERATURE" in c and not c.endswith("_invalid")]
        rh_cols = [c for c in df.columns if "RELATIVE_HUMIDITY" in c and not c.endswith("_invalid")]
        for tc in temp_cols:
            df.loc[idx, tc] -= 6.0
        for rc in rh_cols:
            df.loc[idx, rc] = min(100.0, df.loc[idx, rc] + 30.0)
        df.loc[idx, "is_fault"] = 0
        df.loc[idx, "fault_type"] = "WEATHER_EXTREME"
        df.loc[idx, "fault_id"] = "EVENT_WEATHER_EXTREME"
        df.loc[idx, "target_sensor"] = "CONSENSUS_ALL"
        df.loc[idx, "is_extreme_weather"] = 1
        injected_events_meta.append({
            "fault_id": "EVENT_WEATHER_EXTREME",
            "fault_type": "WEATHER_EXTREME",
            "target_sensor": "CONSENSUS_ALL",
            "start_time": str(f6_time),
            "end_time": str(f6_time),
            "duration_minutes": 30,
            "observations": 1,
            "expected_class": "POSSIBLE_WEATHER_EXTREME",
            "expected_root_cause": "RAPID_COHERENT_WEATHER_EVENT",
            "expected_severity": "MEDIUM"
        })
        print(f"[Injected] EVENT_WEATHER_EXTREME at {f6_time}: -6.0°C and +30% RH on ALL 3 heights simultaneously")

    # ----------------------------------------------------
    # Save Artifacts
    # ----------------------------------------------------
    os.makedirs("data/processed", exist_ok=True)

    # Synchronize canonical columns with raw columns
    COLUMN_MAP = {
        "temp_2m": "AIR_TEMPERATURE1(°C at 2m height)",
        "temp_4m": "AIR_TEMPERATURE2(°C at 4m height)",
        "temp_8m": "AIR_TEMPERATURE3(°C at 8m height)",
        "rh_2m": "RELATIVE_HUMIDITY1(% at 2m height)",
        "rh_4m": "RELATIVE_HUMIDITY2(% at 4m height)",
        "rh_8m": "RELATIVE_HUMIDITY3(% at 8m height)",
        "wind_speed_3m": "WIND_SPEED1(m/s at 3m height) ",
        "wind_speed_6m": "WIND_SPEED2(m/s at 6m height)",
        "wind_speed_10m": "WIND_SPEED3(m/s at 10m height)",
        "wind_dir_3m": "WIND_DIRECTION1(deg at 3m height)",
        "wind_dir_6m": "WIND_DIRECTION2(deg at 6m height)",
        "wind_dir_10m": "WIND_DIRECTION3(deg at 10m height)",
        "pressure": "ATMOSPHERIC_PRESSURE(mbar) ",
        "battery_voltage": "BATTRY_VOLTAGE(V)",
        "rainfall": "RAINFALL(mm)",
    }
    for alias, raw_col in COLUMN_MAP.items():
        if raw_col in df.columns:
            df[alias] = pd.to_numeric(df[raw_col], errors="coerce")

    # Save faulty clean dataset
    clean_cols = [c for c in df.columns if c not in ["is_fault", "fault_type", "fault_id", "target_sensor", "is_extreme_weather"]]
    df[clean_cols].to_csv(OUTPUT_FAULTY, index=False)
    print(f"\nSaved faulty clean dataset: {OUTPUT_FAULTY}")


    # Save ground truth labels
    labels_df = df[["timestamp", "is_fault", "fault_type", "fault_id", "target_sensor", "is_extreme_weather"]].copy()
    labels_df.to_csv(OUTPUT_LABELS, index=False)
    print(f"Saved ground truth fault labels: {OUTPUT_LABELS}")

    # Save event metadata
    events_df = pd.DataFrame(injected_events_meta)
    events_df.to_csv(OUTPUT_EVENTS, index=False)
    print(f"Saved injected event metadata: {OUTPUT_EVENTS}")

    print("\nInjected Events Summary:")
    print(events_df[["fault_id", "fault_type", "target_sensor", "observations", "expected_root_cause", "expected_class"]].to_string(index=False))


if __name__ == "__main__":
    inject_synthetic_faults()
