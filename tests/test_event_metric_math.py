import pandas as pd
from datetime import datetime, timedelta


def match_events(gt_events: pd.DataFrame, pred_events: pd.DataFrame):
    """
    Genuine temporal event matching between ground-truth and predicted events.
    """
    matched_preds = 0
    unmatched_preds = 0
    detected_gts = 0

    for _, p in pred_events.iterrows():
        p_s = p["start_time"]
        p_e = p["end_time"]
        matched = False
        for _, g in gt_events.iterrows():
            g_s = g["start_time"]
            g_e = g["end_time"]
            if max(p_s, g_s) <= min(p_e, g_e):
                matched = True
                break
        if matched:
            matched_preds += 1
        else:
            unmatched_preds += 1

    for _, g in gt_events.iterrows():
        g_s = g["start_time"]
        g_e = g["end_time"]
        detected = False
        for _, p in pred_events.iterrows():
            p_s = p["start_time"]
            p_e = p["end_time"]
            if max(p_s, g_s) <= min(p_e, g_e):
                detected = True
                break
        if detected:
            detected_gts += 1

    n_gt = len(gt_events)
    n_pred = len(pred_events)

    prec = matched_preds / n_pred if n_pred > 0 else 0.0
    rec = detected_gts / n_gt if n_gt > 0 else 0.0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    return {
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "tp_pred": matched_preds,
        "fp_pred": unmatched_preds,
        "fn_gt": n_gt - detected_gts
    }


def test_event_precision_penalizes_false_positives():
    """
    Proves that when 1 true fault is detected but 3 false-positive events are generated,
    event precision is 0.25 (25%), NOT artificially set to 1.0 (100%).
    """
    # 1 Ground truth fault event
    gt = pd.DataFrame([{
        "fault_id": "FAULT_01",
        "start_time": datetime(2024, 6, 1, 12, 0),
        "end_time": datetime(2024, 6, 1, 14, 0),
    }])

    # 4 Predicted events: 1 matching the fault, 3 outside (false positives)
    preds = pd.DataFrame([
        {
            "event_id": 1,
            "start_time": datetime(2024, 6, 1, 12, 30),
            "end_time": datetime(2024, 6, 1, 13, 30),
        },
        {
            "event_id": 2,
            "start_time": datetime(2024, 6, 1, 18, 0),
            "end_time": datetime(2024, 6, 1, 19, 0),
        },
        {
            "event_id": 3,
            "start_time": datetime(2024, 6, 2, 2, 0),
            "end_time": datetime(2024, 6, 2, 3, 0),
        },
        {
            "event_id": 4,
            "start_time": datetime(2024, 6, 2, 8, 0),
            "end_time": datetime(2024, 6, 2, 9, 0),
        },
    ])

    res = match_events(gt, preds)

    assert res["tp_pred"] == 1
    assert res["fp_pred"] == 3
    assert res["recall"] == 1.0
    # Precision MUST be 1 / 4 = 0.25, proving the hardcoded 1.0 flaw is fixed!
    assert res["precision"] == 0.25
    assert abs(res["f1"] - (2 * 0.25 * 1.0 / 1.25)) < 1e-4


def test_event_recall_penalizes_missed_faults():
    """
    Proves that when 2 ground truth faults occur and only 1 is detected,
    recall is 0.50 (50%).
    """
    gt = pd.DataFrame([
        {
            "fault_id": "FAULT_01",
            "start_time": datetime(2024, 6, 1, 12, 0),
            "end_time": datetime(2024, 6, 1, 14, 0),
        },
        {
            "fault_id": "FAULT_02",
            "start_time": datetime(2024, 6, 2, 10, 0),
            "end_time": datetime(2024, 6, 2, 12, 0),
        },
    ])

    preds = pd.DataFrame([
        {
            "event_id": 1,
            "start_time": datetime(2024, 6, 1, 12, 30),
            "end_time": datetime(2024, 6, 1, 13, 30),
        }
    ])

    res = match_events(gt, preds)
    assert res["tp_pred"] == 1
    assert res["fp_pred"] == 0
    assert res["fn_gt"] == 1
    assert res["precision"] == 1.0
    assert res["recall"] == 0.50
