from __future__ import annotations

import numpy as np


def diurnal_anomaly(
    local_solar_time_hour: np.ndarray | float,
    amplitude_k: np.ndarray | float,
    peak_hour: np.ndarray | float,
) -> np.ndarray:
    time, amplitude, peak = np.broadcast_arrays(
        np.asarray(local_solar_time_hour, dtype=np.float64),
        np.asarray(amplitude_k, dtype=np.float64),
        np.asarray(peak_hour, dtype=np.float64),
    )
    return amplitude * np.cos(2.0 * np.pi * (time - peak) / 24.0)


def normalize_local_solar_time(
    temperature_k: np.ndarray,
    local_solar_time_hour: np.ndarray,
    amplitude_k: np.ndarray,
    peak_hour: np.ndarray,
    *,
    reference_hour: float,
) -> np.ndarray:
    observed = diurnal_anomaly(local_solar_time_hour, amplitude_k, peak_hour)
    reference = diurnal_anomaly(reference_hour, amplitude_k, peak_hour)
    return np.asarray(temperature_k, dtype=np.float64) + reference - observed

