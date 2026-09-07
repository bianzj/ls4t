"""Multi-angle component-temperature inversion in radiance space."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .quality import QualityFlag, new_flags, set_flag
from .radiometry import inverse_planck


@dataclass(frozen=True)
class ComponentRetrievalResult:
    temperature_k: np.ndarray
    radiance: np.ndarray
    residual_rms: np.ndarray
    condition_number: np.ndarray
    quality_flag: np.ndarray


def retrieve_components(
    observed_radiance: np.ndarray,
    effective_weights: np.ndarray,
    wavelength_um: float,
    *,
    observation_uncertainty: np.ndarray | None = None,
    ridge: float = 0.0,
    max_condition_number: float = 1.0e6,
    valid_temperature_range_k: tuple[float, float] = (200.0, 380.0),
) -> ComponentRetrievalResult:
    """Solve ``weights @ component_radiance = observed_radiance`` per pixel.

    The last radiance axis is observation/angle and the final weights axes are
    ``(observation, component)``. Invalid observations are omitted per pixel.
    """
    y = np.asarray(observed_radiance, dtype=np.float64)
    matrix = np.asarray(effective_weights, dtype=np.float64)
    if matrix.ndim < 2 or y.shape != matrix.shape[:-1]:
        raise ValueError("effective_weights must have shape (..., observation, component)")
    spatial_shape = y.shape[:-1]
    n_obs, n_components = matrix.shape[-2:]
    if n_obs < n_components:
        raise ValueError("at least as many observations as components are required")
    if ridge < 0:
        raise ValueError("ridge must be non-negative")

    if observation_uncertainty is None:
        sigma = np.ones_like(y)
    else:
        sigma = np.broadcast_to(np.asarray(observation_uncertainty, dtype=np.float64), y.shape)

    flat_y = y.reshape(-1, n_obs)
    flat_a = matrix.reshape(-1, n_obs, n_components)
    flat_sigma = sigma.reshape(-1, n_obs)
    solved = np.full((flat_y.shape[0], n_components), np.nan)
    residual = np.full(flat_y.shape[0], np.nan)
    condition = np.full(flat_y.shape[0], np.nan)
    flags = new_flags((flat_y.shape[0],))

    for index, (values, design, errors) in enumerate(zip(flat_y, flat_a, flat_sigma)):
        valid = (
            np.isfinite(values)
            & np.all(np.isfinite(design), axis=1)
            & np.isfinite(errors)
            & (errors > 0)
        )
        if valid.sum() < n_components:
            flags[index] |= np.uint16(QualityFlag.INPUT_INVALID | QualityFlag.RETRIEVAL_FAILED)
            continue
        weighted_a = design[valid] / errors[valid, None]
        weighted_y = values[valid] / errors[valid]
        condition[index] = np.linalg.cond(weighted_a)
        if not np.isfinite(condition[index]) or condition[index] > max_condition_number:
            flags[index] |= np.uint16(QualityFlag.ILL_CONDITIONED | QualityFlag.RETRIEVAL_FAILED)
            continue
        try:
            if ridge:
                lhs = weighted_a.T @ weighted_a + ridge * np.eye(n_components)
                rhs = weighted_a.T @ weighted_y
                solution = np.linalg.solve(lhs, rhs)
            else:
                solution = np.linalg.lstsq(weighted_a, weighted_y, rcond=None)[0]
        except np.linalg.LinAlgError:
            flags[index] |= np.uint16(QualityFlag.RETRIEVAL_FAILED)
            continue
        if np.any(solution <= 0):
            flags[index] |= np.uint16(QualityFlag.OUT_OF_RANGE | QualityFlag.RETRIEVAL_FAILED)
            continue
        solved[index] = solution
        difference = design[valid] @ solution - values[valid]
        residual[index] = np.sqrt(np.mean(difference**2))

    temperatures = inverse_planck(wavelength_um, solved)
    low, high = valid_temperature_range_k
    bad_temperature = np.any(
        ~np.isfinite(temperatures) | (temperatures < low) | (temperatures > high), axis=1
    )
    set_flag(flags, bad_temperature, QualityFlag.OUT_OF_RANGE)
    temperatures[bad_temperature] = np.nan
    solved[bad_temperature] = np.nan
    return ComponentRetrievalResult(
        temperature_k=temperatures.reshape(spatial_shape + (n_components,)),
        radiance=solved.reshape(spatial_shape + (n_components,)),
        residual_rms=residual.reshape(spatial_shape),
        condition_number=condition.reshape(spatial_shape),
        quality_flag=flags.reshape(spatial_shape),
    )


def retrieve_components_window(
    observed_radiance: np.ndarray,
    effective_weights: np.ndarray,
    wavelength_um: float,
    *,
    window_size: int = 5,
    observation_uncertainty: np.ndarray | None = None,
    ridge: float = 0.0,
    max_condition_number: float = 1.0e6,
    valid_temperature_range_k: tuple[float, float] = (200.0, 380.0),
) -> ComponentRetrievalResult:
    """Window LSCT for cases with fewer angles than components.

    Component radiances are assumed locally constant inside each moving window,
    while effective-emissivity weights may vary by pixel and angle. This is the
    production baseline corresponding to the legacy 5x5 constant-window solves.
    """
    values = np.asarray(observed_radiance, dtype=np.float64)
    weights = np.asarray(effective_weights, dtype=np.float64)
    if values.ndim != 3 or weights.ndim != 4 or weights.shape[:-1] != values.shape:
        raise ValueError(
            "window retrieval requires radiance (row, col, observation) and weights "
            "(row, col, observation, component)"
        )
    if window_size < 1 or window_size % 2 == 0:
        raise ValueError("window_size must be a positive odd integer")
    if observation_uncertainty is None:
        errors = np.ones_like(values)
    else:
        errors = np.broadcast_to(np.asarray(observation_uncertainty, dtype=np.float64), values.shape)

    rows, columns, _ = values.shape
    n_components = weights.shape[-1]
    radius = window_size // 2
    padded_values = np.pad(values, ((radius, radius), (radius, radius), (0, 0)), constant_values=np.nan)
    padded_weights = np.pad(
        weights,
        ((radius, radius), (radius, radius), (0, 0), (0, 0)),
        constant_values=np.nan,
    )
    padded_errors = np.pad(errors, ((radius, radius), (radius, radius), (0, 0)), constant_values=np.nan)
    temperature = np.full((rows, columns, n_components), np.nan)
    radiance = np.full_like(temperature, np.nan)
    residual = np.full((rows, columns), np.nan)
    condition = np.full((rows, columns), np.nan)
    flags = new_flags((rows, columns))

    for row in range(rows):
        for column in range(columns):
            window = (slice(row, row + window_size), slice(column, column + window_size))
            local_values = padded_values[window].reshape(-1)
            local_weights = padded_weights[window].reshape(-1, n_components)
            local_errors = padded_errors[window].reshape(-1)
            result = retrieve_components(
                local_values,
                local_weights,
                wavelength_um,
                observation_uncertainty=local_errors,
                ridge=ridge,
                max_condition_number=max_condition_number,
                valid_temperature_range_k=valid_temperature_range_k,
            )
            temperature[row, column] = result.temperature_k
            radiance[row, column] = result.radiance
            residual[row, column] = result.residual_rms
            condition[row, column] = result.condition_number
            flags[row, column] = result.quality_flag
    return ComponentRetrievalResult(temperature, radiance, residual, condition, flags)
