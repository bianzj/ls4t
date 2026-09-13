import numpy as np
import pytest

from base.lsct import retrieve_components, retrieve_components_window
from base.lst import SplitWindowModel
from base.quality import QualityFlag
from base.radiometry import planck_radiance


def test_split_window_eight_feature_model():
    coefficients = np.zeros((2, 1, 8))
    coefficients[..., 1] = 1.0
    model = SplitWindowModel(np.array([0.0, 60.0]), np.array([0.0, 5.0]), coefficients)
    result = model.retrieve(
        np.array([300.0, 302.0]),
        np.array([298.0, 300.0]),
        0.98,
        0.97,
        2.0,
        30.0,
    )
    np.testing.assert_allclose(result.temperature_k, [299.0, 301.0])
    assert np.all(result.quality_flag == 0)


def test_split_window_rejects_outside_calibration_domain():
    coefficients = np.zeros((2, 1, 8))
    model = SplitWindowModel(np.array([0.0, 60.0]), np.array([0.0, 5.0]), coefficients)
    result = model.retrieve(300.0, 299.0, 0.98, 0.97, 6.0, 30.0)
    assert np.isnan(result.temperature_k)
    assert int(result.quality_flag) & int(QualityFlag.INPUT_INVALID)


def test_split_window_requires_interpolation_grids():
    with pytest.raises(ValueError, match="at least two"):
        SplitWindowModel(np.array([0.0]), np.array([0.0, 5.0]), np.zeros((1, 1, 8)))


def test_two_component_radiance_retrieval():
    expected_temperature = np.array([300.0, 310.0])
    component_radiance = planck_radiance(10.8, expected_temperature)
    weights = np.array([[0.8, 0.2], [0.35, 0.65], [0.1, 0.9]])
    observation = weights @ component_radiance
    result = retrieve_components(observation, weights, 10.8)
    np.testing.assert_allclose(result.temperature_k, expected_temperature, atol=1e-9)
    assert result.residual_rms < 1e-10
    assert result.quality_flag == 0


def test_component_retrieval_flags_singular_matrix():
    weights = np.ones((2, 2))
    result = retrieve_components(np.array([8.0, 8.0]), weights, 10.8)
    assert np.all(np.isnan(result.temperature_k))
    assert int(result.quality_flag) & int(QualityFlag.ILL_CONDITIONED)


def test_window_retrieval_supports_more_components_than_angles():
    expected_temperature = np.array([295.0, 305.0, 315.0])
    component_radiance = planck_radiance(10.8, expected_temperature)
    weights = np.empty((3, 3, 2, 3))
    for row in range(3):
        for column in range(3):
            first = 0.15 + 0.1 * row
            second = 0.2 + 0.1 * column
            weights[row, column, 0] = [first, second, 1.0 - first - second]
            weights[row, column, 1] = [second, 0.65 - 0.05 * row, 0.35 + 0.05 * row - second]
    observation = np.einsum("...oc,c->...o", weights, component_radiance)
    result = retrieve_components_window(observation, weights, 10.8, window_size=3)
    np.testing.assert_allclose(result.temperature_k[1, 1], expected_temperature, atol=1e-8)
    assert result.quality_flag[1, 1] == 0
