"""
Self-Healing & Data Imputation Engine for Automatic Weather Stations.
Solves the SIH Grand Challenge: "Can AI build a self-healing weather network?"

When a sensor fault is detected (Spike, Frozen, Out of bounds, NaN):
  1. Reconstructs missing/faulty measurements using thermodynamic Magnus coupling
     between Temperature, Relative Humidity, and recent Dew Point baselines.
  2. Falls back to causal autoregressive rolling median when multivariate partner is unavailable.
  3. Emits both original reading, healed reading, and a self_healed flag.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np

MAGNUS_A = 17.27
MAGNUS_B = 237.7


def estimate_temperature_from_rh(rh: float, recent_dew_point: float) -> float:
    """Estimates nominal air temperature given healthy relative humidity and recent dew point."""
    rh_clipped = np.clip(rh, 5.0, 100.0)
    alpha_dp = (MAGNUS_A * recent_dew_point) / (MAGNUS_B + recent_dew_point)
    gamma = alpha_dp - np.log(rh_clipped / 100.0)
    if (MAGNUS_A - gamma) == 0:
        return recent_dew_point
    est_temp = (MAGNUS_B * gamma) / (MAGNUS_A - gamma)
    return float(np.clip(est_temp, 5.0, 50.0))


def estimate_rh_from_temperature(temp: float, recent_dew_point: float) -> float:
    """Estimates nominal relative humidity given healthy temperature and recent dew point."""
    alpha_dp = (MAGNUS_A * recent_dew_point) / (MAGNUS_B + recent_dew_point)
    alpha_t = (MAGNUS_A * temp) / (MAGNUS_B + temp)
    rh_est = 100.0 * np.exp(alpha_dp - alpha_t)
    return float(np.clip(rh_est, 10.0, 100.0))


def heal_observation(
    temp: Optional[float],
    rh: Optional[float],
    press: Optional[float],
    fault_type: str = "NONE",
    culprit_sensor: str = "NONE",
    history: Optional[List[Tuple[float, float, float]]] = None
) -> Dict[str, Any]:
    """
    Imputes/heals an anomalous weather station observation.
    
    Returns:
        Dictionary with original values, corrected/healed values, and healing metadata.
    """
    history_pts = history or []
    recent_temps = [p[0] for p in history_pts if p[0] is not None and not np.isnan(p[0]) and 5.0 <= p[0] <= 50.0]
    recent_rhs = [p[1] for p in history_pts if p[1] is not None and not np.isnan(p[1]) and 5.0 <= p[1] <= 100.0]
    recent_presses = [p[2] for p in history_pts if p[2] is not None and not np.isnan(p[2]) and 890.0 <= p[2] <= 1050.0]

    # Baseline medians
    med_t = float(np.median(recent_temps)) if recent_temps else 28.5
    med_rh = float(np.median(recent_rhs)) if recent_rhs else 65.0
    med_p = float(np.median(recent_presses)) if recent_presses else 985.0

    # Recent dew point baseline
    alpha = ((MAGNUS_A * med_t) / (MAGNUS_B + med_t)) + np.log(max(med_rh, 1.0) / 100.0)
    recent_dp = float((MAGNUS_B * alpha) / (MAGNUS_A - alpha))

    healed_t = temp
    healed_rh = rh
    healed_p = press
    is_healed = False
    healing_method = "NONE"
    healed_channel = "NONE"

    # 1. Temperature Fault Healing
    temp_is_bad = (
        temp is None or np.isnan(temp) or
        temp > 55.0 or temp < 5.0 or
        culprit_sensor == "Temperature" or
        "TEMP" in fault_type.upper()
    )
    if temp_is_bad:
        if rh is not None and not np.isnan(rh) and 10.0 <= rh <= 100.0:
            healed_t = round(estimate_temperature_from_rh(rh, recent_dp), 2)
            healing_method = "THERMODYNAMIC_MAGNUS_INVERSION"
        else:
            healed_t = round(med_t, 2)
            healing_method = "AUTOREGRESSIVE_MEDIAN"
        is_healed = True
        healed_channel = "Temperature"

    # 2. Humidity Fault Healing
    rh_is_bad = (
        rh is None or np.isnan(rh) or
        rh < 5.0 or rh > 100.0 or
        culprit_sensor == "Humidity" or
        "HUMIDITY" in fault_type.upper()
    )
    if rh_is_bad:
        if healed_t is not None and not np.isnan(healed_t):
            healed_rh = round(estimate_rh_from_temperature(healed_t, recent_dp), 2)
            healing_method = "THERMODYNAMIC_MAGNUS_INVERSION"
        else:
            healed_rh = round(med_rh, 2)
            healing_method = "AUTOREGRESSIVE_MEDIAN"
        is_healed = True
        healed_channel = "Humidity" if healed_channel == "NONE" else "Multi-Sensor"

    # 3. Pressure Fault Healing
    press_is_bad = (
        press is None or np.isnan(press) or
        press < 890.0 or press > 1050.0 or
        culprit_sensor == "Pressure" or
        "PRESSURE" in fault_type.upper()
    )
    if press_is_bad:
        healed_p = round(med_p, 2)
        is_healed = True
        healing_method = "BAROMETRIC_AUTOREGRESSIVE_MEDIAN"
        healed_channel = "Pressure" if healed_channel == "NONE" else "Multi-Sensor"

    return {
        "original_temperature": temp,
        "original_humidity": rh,
        "original_pressure": press,
        "corrected_temperature": healed_t,
        "corrected_humidity": healed_rh,
        "corrected_pressure": healed_p,
        "is_healed": is_healed,
        "healed_channel": healed_channel,
        "healing_method": healing_method
    }
