from typing import Dict, List, Optional, Tuple, Any
import numpy as np

MAGNUS_A = 17.27
MAGNUS_B = 237.7


def estimate_temperature_from_rh(rh: float, recent_dew_point: float) -> Tuple[float, float, str]:
    rh_clipped = float(np.clip(rh, 5.0, 100.0))
    alpha_dp = (MAGNUS_A * recent_dew_point) / (MAGNUS_B + recent_dew_point)
    gamma = alpha_dp - np.log(rh_clipped / 100.0)
    if (MAGNUS_A - gamma) == 0:
        return recent_dew_point, 2.5, "Degenerate vapor limit"
    est_temp = (MAGNUS_B * gamma) / (MAGNUS_A - gamma)
    est_clamped = float(np.clip(est_temp, 5.0, 50.0))
    uncertainty = 0.8 if 20.0 <= rh_clipped <= 90.0 else 1.5
    evidence = f"Magnus psychrometric inversion using conserved dew point ({recent_dew_point:.1f}°C) and valid relative humidity ({rh_clipped:.1f}%)."
    return round(est_clamped, 2), uncertainty, evidence


def estimate_rh_from_temperature(temp: float, recent_dew_point: float) -> Tuple[float, float, str]:
    alpha_dp = (MAGNUS_A * recent_dew_point) / (MAGNUS_B + recent_dew_point)
    alpha_t = (MAGNUS_A * temp) / (MAGNUS_B + temp)
    rh_est = 100.0 * np.exp(alpha_dp - alpha_t)
    rh_clamped = float(np.clip(rh_est, 5.0, 100.0))
    uncertainty = 3.5
    evidence = f"Magnus psychrometric inversion using conserved dew point ({recent_dew_point:.1f}°C) and valid air temperature ({temp:.1f}°C)."
    return round(rh_clamped, 1), uncertainty, evidence


def heal_observation(
    temp: Optional[float],
    rh: Optional[float],
    press: Optional[float],
    fault_type: str = "NONE",
    culprit_sensor: str = "NONE",
    history: Optional[List[Tuple[float, float, float]]] = None
) -> Dict[str, Any]:
    history_pts = history or []
    recent_temps = [p[0] for p in history_pts if p[0] is not None and not np.isnan(p[0]) and 5.0 <= p[0] <= 50.0]
    recent_rhs = [p[1] for p in history_pts if p[1] is not None and not np.isnan(p[1]) and 5.0 <= p[1] <= 100.0]
    recent_presses = [p[2] for p in history_pts if p[2] is not None and not np.isnan(p[2]) and 890.0 <= p[2] <= 1050.0]

    med_t = float(np.median(recent_temps)) if recent_temps else 28.5
    med_rh = float(np.median(recent_rhs)) if recent_rhs else 65.0
    med_p = float(np.median(recent_presses)) if recent_presses else 985.0

    recent_dp_valid = False
    recent_dp = 20.0
    if len(recent_temps) >= 2 and len(recent_rhs) >= 2:
        alpha = ((MAGNUS_A * med_t) / (MAGNUS_B + med_t)) + np.log(max(med_rh, 1.0) / 100.0)
        recent_dp = float((MAGNUS_B * alpha) / (MAGNUS_A - alpha))
        if 0.0 <= recent_dp <= 35.0:
            recent_dp_valid = True

    healed_t = temp
    healed_rh = rh
    healed_p = press
    is_healed = False
    healing_method = "NONE"
    healed_channel = "NONE"
    uncertainty: Optional[float] = None
    evidence_desc = "No reconstruction required. Observations conform to physical boundaries."
    reconstruction_grade = "VALIDATED_PHYSICAL"

    temp_is_bad = (
        temp is None or np.isnan(temp) or
        temp > 55.0 or temp < 5.0 or
        culprit_sensor in ["Temperature", "all"] or
        "TEMP" in fault_type.upper() or
        "SPIKE" in fault_type.upper() or
        "FROZEN" in fault_type.upper() or
        "COMMUNICATION" in fault_type.upper()
    )

    rh_is_bad = (
        rh is None or np.isnan(rh) or
        rh < 5.0 or rh > 100.0 or
        culprit_sensor in ["Humidity", "all"] or
        "HUMIDITY" in fault_type.upper() or
        "COMMUNICATION" in fault_type.upper()
    )

    press_is_bad = (
        press is None or np.isnan(press) or
        press < 890.0 or press > 1050.0 or
        culprit_sensor in ["Pressure", "all"] or
        "PRESSURE" in fault_type.upper() or
        "COMMUNICATION" in fault_type.upper()
    )

    if temp_is_bad:
        is_healed = True
        healed_channel = "Temperature"
        if not rh_is_bad and rh is not None and recent_dp_valid:
            healed_t, uncertainty, evidence_desc = estimate_temperature_from_rh(rh, recent_dp)
            healing_method = "THERMODYNAMIC_MAGNUS_INVERSION"
            reconstruction_grade = "HIGH_CONFIDENCE_PHYSICAL"
        else:
            healed_t = round(med_t, 2)
            uncertainty = 1.8
            healing_method = "AUTOREGRESSIVE_MEDIAN"
            reconstruction_grade = "MODERATE_CONFIDENCE_AUTOREGRESSIVE"
            evidence_desc = f"Channel RH is compromised or dew point is unverified. Restored via robust rolling median ({med_t:.1f}°C) over window of {len(recent_temps)} observations."

    if rh_is_bad:
        is_healed = True
        healed_channel = "Humidity" if not temp_is_bad else "Multi-Channel (T + RH)"
        if not temp_is_bad and temp is not None and recent_dp_valid:
            healed_rh, uncertainty_rh, evidence_rh = estimate_rh_from_temperature(temp, recent_dp)
            healing_method = "THERMODYNAMIC_MAGNUS_INVERSION"
            reconstruction_grade = "HIGH_CONFIDENCE_PHYSICAL"
            evidence_desc = evidence_rh
            uncertainty = uncertainty_rh if uncertainty is None else max(uncertainty, uncertainty_rh)
        else:
            healed_rh = round(med_rh, 1)
            healing_method = "AUTOREGRESSIVE_MEDIAN"
            reconstruction_grade = "MODERATE_CONFIDENCE_AUTOREGRESSIVE"
            uncertainty = 5.0 if uncertainty is None else max(uncertainty, 5.0)
            evidence_desc = f"Restored via rolling median ({med_rh:.1f}%) over window of {len(recent_rhs)} observations."

    if press_is_bad:
        is_healed = True
        healed_channel = "Pressure" if healed_channel == "NONE" else f"{healed_channel} + Pressure"
        healed_p = round(med_p, 1)
        healing_method = "AUTOREGRESSIVE_MEDIAN" if healing_method == "NONE" else f"{healing_method} + BAROMETRIC_MEDIAN"
        reconstruction_grade = "MODERATE_CONFIDENCE_AUTOREGRESSIVE"
        uncertainty = 0.8 if uncertainty is None else max(uncertainty, 0.8)
        evidence_desc = f"Barometric pressure restored to local station elevation baseline ({med_p:.1f} hPa)."

    return {
        "is_healed": is_healed,
        "healing_method": healing_method,
        "healed_channel": healed_channel,
        "fault_type": fault_type,
        "reconstruction_grade": reconstruction_grade,
        "uncertainty_estimate": uncertainty,
        "supporting_evidence": evidence_desc,
        "corrected_temperature": healed_t,
        "corrected_humidity": healed_rh,
        "corrected_pressure": healed_p,
        "original_temperature": temp,
        "original_humidity": rh,
        "original_pressure": press
    }
