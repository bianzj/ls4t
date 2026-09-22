from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..quality import QualityFlag, new_flags, set_flag
from .directional import normalize_directional
from .harmonization import SensorHarmonization
from .profile import NormalizationProfile
from .temporal import normalize_local_solar_time


@dataclass(frozen=True)
class NormalizationInput:
    sensor: str
    grid_id: str
    temporal_interval: str
    temperature_k: np.ndarray
    uncertainty_k: np.ndarray
    view_zenith_deg: np.ndarray
    solar_zenith_deg: np.ndarray
    relative_azimuth_deg: np.ndarray
    local_solar_time_hour: np.ndarray
    directional_coefficients_k: np.ndarray
    diurnal_amplitude_k: np.ndarray
    diurnal_peak_hour: np.ndarray
    quality_flag: np.ndarray | None = None


@dataclass(frozen=True)
class NormalizationResult:
    sensor: str
    temperature_k: np.ndarray
    uncertainty_k: np.ndarray
    quality_flag: np.ndarray
    profile: NormalizationProfile


def normalize_temperature(
    source: NormalizationInput,
    profile: NormalizationProfile,
    *,
    harmonization: SensorHarmonization | None = None,
) -> NormalizationResult:
    if source.grid_id != profile.grid_id:
        raise ValueError(f"input grid {source.grid_id!r} does not match profile grid {profile.grid_id!r}")
    if source.temporal_interval != profile.temporal_interval:
        raise ValueError(
            f"input interval {source.temporal_interval!r} does not match profile interval "
            f"{profile.temporal_interval!r}"
        )
    values = np.asarray(source.temperature_k, dtype=np.float64)
    uncertainty = np.broadcast_to(
        np.asarray(source.uncertainty_k, dtype=np.float64), values.shape
    ).copy()
    vza = np.broadcast_to(np.asarray(source.view_zenith_deg, dtype=np.float64), values.shape)
    sza = np.broadcast_to(np.asarray(source.solar_zenith_deg, dtype=np.float64), values.shape)
    raa = np.broadcast_to(np.asarray(source.relative_azimuth_deg, dtype=np.float64), values.shape)
    local_time = np.broadcast_to(
        np.asarray(source.local_solar_time_hour, dtype=np.float64), values.shape
    )
    directional_coefficients = np.broadcast_to(
        np.asarray(source.directional_coefficients_k, dtype=np.float64), values.shape + (3,)
    )
    amplitude = np.broadcast_to(np.asarray(source.diurnal_amplitude_k, dtype=np.float64), values.shape)
    peak_hour = np.broadcast_to(np.asarray(source.diurnal_peak_hour, dtype=np.float64), values.shape)
    if source.quality_flag is None:
        flags = new_flags(values.shape)
    else:
        flags = np.broadcast_to(np.asarray(source.quality_flag, dtype=np.uint16), values.shape).copy()
    invalid = (
        ~np.isfinite(values)
        | ~np.isfinite(uncertainty)
        | (uncertainty <= 0)
        | ~np.isfinite(vza)
        | (np.abs(vza) >= 89.0)
        | ~np.isfinite(sza)
        | (sza < 0)
        | (sza > 180)
        | ~np.isfinite(raa)
        | ~np.isfinite(local_time)
        | (local_time < 0)
        | (local_time >= 24)
        | ~np.all(np.isfinite(directional_coefficients), axis=-1)
        | ~np.isfinite(amplitude)
        | (amplitude < 0)
        | ~np.isfinite(peak_hour)
        | (peak_hour < 0)
        | (peak_hour >= 24)
    )
    set_flag(flags, invalid, QualityFlag.INPUT_INVALID)

    values = normalize_directional(
        values,
        vza,
        sza,
        raa,
        directional_coefficients,
        reference_view_zenith_deg=profile.reference_view_zenith_deg,
        reference_solar_zenith_deg=profile.reference_solar_zenith_deg,
        reference_relative_azimuth_deg=profile.reference_relative_azimuth_deg,
    )
    values = normalize_local_solar_time(
        values,
        local_time,
        amplitude,
        peak_hour,
        reference_hour=profile.reference_local_solar_time_hour,
    )
    if harmonization is not None:
        if harmonization.sensor.upper() != source.sensor.upper():
            raise ValueError("harmonization sensor does not match normalization input")
        values, uncertainty = harmonization.apply(values, uncertainty)

    failed = ~np.isfinite(values) | (values < 150.0) | (values > 400.0)
    set_flag(flags, failed, QualityFlag.NORMALIZATION_FAILED)
    values = np.where(invalid | failed, np.nan, values)
    uncertainty = np.where(invalid | failed, np.nan, uncertainty)
    return NormalizationResult(source.sensor, values, uncertainty, flags, profile)
