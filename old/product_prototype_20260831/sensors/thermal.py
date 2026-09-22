"""Shared adapter for AATSR/SLSTR-style dual-channel L2LST production."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..physics.canopy import effective_emissivity, vegetation_fraction_from_lai
from ..retrieval.lst import SplitWindowModel, SplitWindowResult


@dataclass(frozen=True)
class DualChannelObservation:
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
