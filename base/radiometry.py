"""Radiometric conversions with explicit units.

Wavelength is in micrometres, temperature in kelvin and spectral radiance in
W m-2 sr-1 um-1. Unlike the legacy helper, Celsius is never guessed.
"""

from __future__ import annotations

import numpy as np

C1_UM = 1.191042972e8
C2_UM_K = 1.438776877e4


def planck_radiance(wavelength_um: float, temperature_k: np.ndarray | float) -> np.ndarray:
    wavelength = float(wavelength_um)
    temperature = np.asarray(temperature_k, dtype=np.float64)
    if wavelength <= 0:
        raise ValueError("wavelength_um must be positive")
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        result = C1_UM / (
            wavelength**5 * np.expm1(C2_UM_K / (wavelength * temperature))
        )
    return np.where(temperature > 0, result, np.nan)


def inverse_planck(wavelength_um: float, radiance: np.ndarray | float) -> np.ndarray:
    wavelength = float(wavelength_um)
    values = np.asarray(radiance, dtype=np.float64)
    if wavelength <= 0:
        raise ValueError("wavelength_um must be positive")
    with np.errstate(divide="ignore", invalid="ignore"):
        result = C2_UM_K / (
            wavelength * np.log1p(C1_UM / (values * wavelength**5))
        )
    return np.where(values > 0, result, np.nan)


def decode_temperature(
    raw: np.ndarray,
    *,
    scale: float,
    offset: float = 0.0,
    fill_value: int | float | None = None,
    source_unit: str = "K",
) -> np.ndarray:
    """Decode a stored temperature into kelvin; this is unit decoding, not L3N."""
    source = np.asarray(raw)
    result = source.astype(np.float64) * scale + offset
    if source_unit.lower() in {"c", "degc", "celsius"}:
        result += 273.15
    elif source_unit.lower() not in {"k", "kelvin"}:
        raise ValueError(f"unsupported temperature unit: {source_unit}")
    if fill_value is not None:
        result = np.where(source == fill_value, np.nan, result)
    return result


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
import numpy as np


planck_c1 = 11910.439340652


planck_c2 = 14388.291040407


temperature_threshold = 100


temperature_zero = 273.15


def planck(wavelength, Ts):
    '''
    基于planck公式，计算某个波长时候，从温度到辐射的转换
    :param wavelength: 波长，10.5
    :param Ts: 温度，可以是亮温，也可以是摄氏度
    :return: 辐射
    '''
    c1 = planck_c1
    c2 = planck_c2
    if np.isscalar(Ts):
        if Ts < temperature_threshold:
            Ts = Ts + temperature_zero
        wavelength = np.float64(wavelength)
        Ts = float(Ts)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    else:
        Ts = np.array(Ts, dtype=np.float64)
        Ts[Ts < temperature_threshold] = Ts[Ts < temperature_threshold] + temperature_zero
        wavelength = float(wavelength)
        rad = c1 / (np.power(wavelength, 5) * (np.exp(c2 / Ts / wavelength) - 1)) * 10000
    return rad


def inv_planck(wavelength, rad):
    '''
    基于planck公式，计算从辐射到亮温的转换
    :param wavelength: 波长,10.5
    :param rad: 辐射
    :return: 亮温 （300）
    '''
    c1 = planck_c1 * 10000
    c2 = planck_c2
    temp = c1 / (rad * np.power((wavelength), 5)) + 1
    Ts = c2 / (wavelength * np.log(temp))
    return Ts

