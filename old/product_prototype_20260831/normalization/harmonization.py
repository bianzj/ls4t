from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SensorHarmonization:
    sensor: str
    reference_sensor: str
    slope: float = 1.0
    offset_k: float = 0.0
    calibration_uncertainty_k: float = 0.0

    def apply(
        self, temperature_k: np.ndarray, uncertainty_k: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        if self.slope <= 0 or self.calibration_uncertainty_k < 0:
            raise ValueError("invalid harmonization coefficients")
        values = self.slope * np.asarray(temperature_k, dtype=np.float64) + self.offset_k
        uncertainty = np.sqrt(
            (self.slope * np.asarray(uncertainty_k, dtype=np.float64)) ** 2
            + self.calibration_uncertainty_k**2
        )
        return values, uncertainty

