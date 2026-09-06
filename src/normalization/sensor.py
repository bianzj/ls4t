from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from base.files import read_npz_payload, write_npz_atomic


# 手动运行参数
SENSOR_INPUT_ROOT = Path("/home/hero/data/ls4t/l3n_space")
SENSOR_OUTPUT_ROOT = Path("/home/hero/data/ls4t/l3n_sensor")
YEAR_TEMPLATE = "{year}"
YEARS = range(2003, 2026)
SENSOR_NAME = "AATSR"
REFERENCE_SENSOR_NAME = "SLSTR"
SLOPE = 1.0
OFFSET_K = 0.0
CALIBRATION_UNCERTAINTY_K = 0.0
OVERWRITE = False


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


def sensor_normalize_years(
    indir_space=None,
    outdir_sensor=None,
    years=None,
    sensor_name=None,
    reference_sensor_name=None,
    slope=None,
    offset_k=None,
    calibration_uncertainty_k=None,
    overwrite=None,
) -> None:
    """按年份手工执行传感器间标定。"""
    if indir_space is None:
        indir_space = SENSOR_INPUT_ROOT
    if outdir_sensor is None:
        outdir_sensor = SENSOR_OUTPUT_ROOT
    if years is None:
        years = YEARS
    if sensor_name is None:
        sensor_name = SENSOR_NAME
    if reference_sensor_name is None:
        reference_sensor_name = REFERENCE_SENSOR_NAME
    if slope is None:
        slope = SLOPE
    if offset_k is None:
        offset_k = OFFSET_K
    if calibration_uncertainty_k is None:
        calibration_uncertainty_k = CALIBRATION_UNCERTAINTY_K
    if overwrite is None:
        overwrite = OVERWRITE
    model = SensorHarmonization(
        sensor_name,
        reference_sensor_name,
        float(slope),
        float(offset_k),
        float(calibration_uncertainty_k),
    )
    for year in years:
        input_year = Path(indir_space) / YEAR_TEMPLATE.format(year=year)
        output_year = Path(outdir_sensor) / YEAR_TEMPLATE.format(year=year)
        for input_path in sorted(input_year.rglob("*.npz")) if input_year.is_dir() else []:
            output_path = output_year / input_path.relative_to(input_year)
            if output_path.exists() and not overwrite:
                continue
            payload = read_npz_payload(input_path)
            payload["temperature_k"], payload["uncertainty_k"] = model.apply(
                payload["temperature_k"], payload["uncertainty_k"]
            )
            write_npz_atomic(output_path, payload)


if __name__ == "__main__":
    sensor_normalize_years()
