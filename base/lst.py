"""Operational generalized split-window LST retrieval.

This retains the eight-feature formulation used by the AATSR implementation,
but removes file loops, global paths and implicit scaling from the algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .quality import QualityFlag, new_flags, set_flag


@dataclass(frozen=True)
class SplitWindowResult:
    temperature_k: np.ndarray
    quality_flag: np.ndarray


@dataclass(frozen=True)
class SplitWindowModel:
    view_zenith_nodes_deg: np.ndarray
    water_vapour_edges: np.ndarray
    coefficients: np.ndarray
    valid_temperature_range_k: tuple[float, float] = (220.0, 365.0)

    def __post_init__(self) -> None:
        vza = np.asarray(self.view_zenith_nodes_deg, dtype=np.float64)
        water = np.asarray(self.water_vapour_edges, dtype=np.float64)
        coeff = np.asarray(self.coefficients, dtype=np.float64)
        if vza.ndim != 1 or water.ndim != 1 or vza.size < 2 or water.size < 2:
            raise ValueError("calibration grids require at least two VZA nodes and two water edges")
        if not np.all(np.isfinite(vza)) or not np.all(np.isfinite(water)):
            raise ValueError("calibration grid nodes must be finite")
        expected = (vza.size, water.size - 1, 8)
        if coeff.shape != expected:
            raise ValueError(f"coefficients must have shape {expected}, got {coeff.shape}")
        if not np.all(np.isfinite(coeff)):
            raise ValueError("calibration coefficients must be finite")
        if np.any(np.diff(vza) <= 0) or np.any(np.diff(water) <= 0):
            raise ValueError("coefficient grid nodes must be strictly increasing")

    def retrieve(
        self,
        bt1_k: np.ndarray,
        bt2_k: np.ndarray,
        emissivity1: np.ndarray,
        emissivity2: np.ndarray,
        water_vapour: np.ndarray,
        view_zenith_deg: np.ndarray,
        *,
        cloud_mask: np.ndarray | None = None,
    ) -> SplitWindowResult:
        bt1, bt2, e1, e2, water, vza = np.broadcast_arrays(
            *[
                np.asarray(value, dtype=np.float64)
                for value in (bt1_k, bt2_k, emissivity1, emissivity2, water_vapour, view_zenith_deg)
            ]
        )
        flags = new_flags(bt1.shape)
        invalid = (
            ~np.isfinite(bt1)
            | ~np.isfinite(bt2)
            | ~np.isfinite(e1)
            | ~np.isfinite(e2)
            | ~np.isfinite(water)
            | ~np.isfinite(vza)
            | (bt1 <= 0)
            | (bt2 <= 0)
            | (e1 <= 0)
            | (e1 > 1)
            | (e2 <= 0)
            | (e2 > 1)
        )
        set_flag(flags, invalid, QualityFlag.INPUT_INVALID)
        if cloud_mask is not None:
            cloud = np.broadcast_to(np.asarray(cloud_mask, dtype=bool), bt1.shape)
            set_flag(flags, cloud, QualityFlag.CLOUD)
            invalid |= cloud

        mean_e = (e1 + e2) / 2.0
        delta_e = e1 - e2
        mean_bt = (bt1 + bt2) / 2.0
        delta_bt = (bt1 - bt2) / 2.0
        with np.errstate(divide="ignore", invalid="ignore"):
            features = np.stack(
                [
                    np.ones_like(bt1),
                    mean_bt,
                    (1.0 - mean_e) / mean_e * mean_bt,
                    delta_e / mean_e**2 * mean_bt,
                    delta_bt,
                    (1.0 - mean_e) / mean_e * delta_bt,
                    delta_e / mean_e**2 * delta_bt,
                    (bt1 - bt2) ** 2,
                ],
                axis=-1,
            )

        vnodes = np.asarray(self.view_zenith_nodes_deg, dtype=np.float64)
        wedges = np.asarray(self.water_vapour_edges, dtype=np.float64)
        lower_v = np.searchsorted(vnodes, vza, side="right") - 1
        lower_v = np.clip(lower_v, 0, vnodes.size - 2)
        water_bin = np.searchsorted(wedges, water, side="right") - 1
        outside = (vza < vnodes[0]) | (vza > vnodes[-1]) | (water < wedges[0]) | (water >= wedges[-1])
        invalid |= outside
        set_flag(flags, outside, QualityFlag.INPUT_INVALID)
        water_bin = np.clip(water_bin, 0, wedges.size - 2)

        coeff = np.asarray(self.coefficients, dtype=np.float64)
        c0 = coeff[lower_v, water_bin]
        c1 = coeff[lower_v + 1, water_bin]
        fraction = (vza - vnodes[lower_v]) / (vnodes[lower_v + 1] - vnodes[lower_v])
        interpolated = c0 * (1.0 - fraction[..., None]) + c1 * fraction[..., None]
        result = np.sum(interpolated * features, axis=-1)
        result = np.where(invalid, np.nan, result)

        low, high = self.valid_temperature_range_k
        out_of_range = np.isfinite(result) & ((result < low) | (result > high))
        set_flag(flags, out_of_range, QualityFlag.OUT_OF_RANGE)
        result[out_of_range] = np.nan
        return SplitWindowResult(result, flags)


def vegetation_fraction_from_lai(
    lai: np.ndarray | float,
    view_zenith_deg: np.ndarray | float,
    projection_g: float = 0.5,
) -> np.ndarray:
    """Convert LAI to directional vegetation fraction."""

    lai_values, vza = np.broadcast_arrays(
        np.asarray(lai, dtype=np.float64),
        np.asarray(view_zenith_deg, dtype=np.float64),
    )
    cosine = np.cos(np.deg2rad(vza))
    valid = (lai_values >= 0) & (np.abs(vza) < 89.0) & (cosine > 0)
    with np.errstate(over="ignore", invalid="ignore"):
        fraction = 1.0 - np.exp(-projection_g * lai_values / cosine)
    return np.where(valid, np.clip(fraction, 0.0, 1.0), np.nan)


def effective_emissivity(
    soil_emissivity: np.ndarray | float,
    vegetation_emissivity: np.ndarray | float,
    vegetation_fraction: np.ndarray | float,
    *,
    scattering_factor: float = 0.75,
    maximum: float = 0.995,
) -> np.ndarray:
    """Calculate mixed-pixel emissivity used by the split-window model."""

    soil, vegetation, fraction = np.broadcast_arrays(
        np.asarray(soil_emissivity, dtype=np.float64),
        np.asarray(vegetation_emissivity, dtype=np.float64),
        np.asarray(vegetation_fraction, dtype=np.float64),
    )
    scattering = (1.0 - soil) * vegetation * scattering_factor * (1.0 - fraction)
    result = soil * (1.0 - fraction) + vegetation * fraction + scattering
    valid = (
        (soil > 0)
        & (soil <= 1)
        & (vegetation > 0)
        & (vegetation <= 1)
        & (fraction >= 0)
        & (fraction <= 1)
    )
    return np.where(valid, np.clip(result, 0.0, maximum), np.nan)


@dataclass(frozen=True)
class DualChannelObservation:
    """Shared in-memory input for AATSR/SLSTR/MSG split-window retrieval."""

    bt1_k: np.ndarray
    bt2_k: np.ndarray
    soil_emissivity1: np.ndarray
    soil_emissivity2: np.ndarray
    vegetation_emissivity1: np.ndarray
    vegetation_emissivity2: np.ndarray
    lai: np.ndarray
    water_vapour: np.ndarray
    view_zenith_deg: np.ndarray
    cloud_mask: np.ndarray | None = None


def retrieve_dual_channel_lst(
    observation: DualChannelObservation,
    model: SplitWindowModel,
    *,
    scattering_factor: float = 0.75,
) -> SplitWindowResult:
    """Run the common split-window physics without owning file traversal."""

    fraction = vegetation_fraction_from_lai(observation.lai, observation.view_zenith_deg)
    emissivity1 = effective_emissivity(
        observation.soil_emissivity1,
        observation.vegetation_emissivity1,
        fraction,
        scattering_factor=scattering_factor,
    )
    emissivity2 = effective_emissivity(
        observation.soil_emissivity2,
        observation.vegetation_emissivity2,
        fraction,
        scattering_factor=scattering_factor,
    )
    return model.retrieve(
        observation.bt1_k,
        observation.bt2_k,
        emissivity1,
        emissivity2,
        observation.water_vapour,
        observation.view_zenith_deg,
        cloud_mask=observation.cloud_mask,
    )
