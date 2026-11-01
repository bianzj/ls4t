"""Controlled numerical contracts; these are not satellite accuracy tests."""
import numpy as np
import pytest

from base.normalization import angle, time
from base.quality import QualityFlag


def test_angle_calibration_recovers_matched_reference_bias():
    vza = np.array([15, 25, 35, 45, 55, 60.])
    sza = np.array([20, 40, 60, 25, 70, 50.])
    raa = np.array([0, 60, 120, 180, 90, 30.])
    sec = 1 / np.cos(np.deg2rad(vza)) - 1
    observed = 300 + sec * (2 + 3 * np.cos(np.deg2rad(raa)) + 4 * np.cos(np.deg2rad(sza)))
    fit = angle.fit_directional_coefficients(observed, np.full(6, 300.), vza, sza, raa)
    np.testing.assert_allclose(fit.coefficients_k, [2, 3, 4], atol=1e-10)
    np.testing.assert_allclose(angle.normalize_directional(observed, vza, sza, raa, fit.coefficients_k), 300)
    assert fit.sample_count == 6
    assert fit.rmse_k < 1e-10


def test_angle_calibration_rejects_unidentifiable_geometry():
    with pytest.raises(ValueError, match="rank|identif"):
        angle.fit_directional_coefficients(np.ones(6)*300, np.ones(6)*300, np.ones(6)*30, 30, 0)


def test_angle_masks_invalid_geometry_and_requires_three_coefficients():
    actual = angle.normalize_directional([300, 300, 300], [0, 90, -1], 30, 0, [2, 0, 0])
    assert actual[0] == 300
    assert np.isnan(actual[1:]).all()
    with pytest.raises(ValueError, match="three"):
        angle.normalize_directional([300], 0, 30, 0, 1.)


def test_diurnal_fit_recovers_amplitude_peak_and_ignores_cloud():
    hours = np.arange(0., 24., 3.)
    values = 290 + 8*np.cos(2*np.pi*(hours-15)/24)
    values[0] = 999
    flags = np.zeros(8, dtype=np.uint16)
    flags[0] = QualityFlag.CLOUD
    fit = time.fit_diurnal_cycle(values, hours, quality_flag=flags)
    assert fit.mean_k == pytest.approx(290)
    assert fit.amplitude_k == pytest.approx(8)
    assert fit.peak_hour == pytest.approx(15)
    assert fit.sample_count == 7
    assert fit.rmse_k < 1e-10
    actual = time.normalize_local_solar_time([294.], [11.], fit.amplitude_k, fit.peak_hour, reference_hour=15.)
    np.testing.assert_allclose(actual, [298.])


def test_diurnal_fit_rejects_short_observation_window():
    with pytest.raises(ValueError, match="span|coverage"):
        time.fit_diurnal_cycle([300, 301, 302, 303], [10, 10.5, 11, 11.5])


@pytest.mark.parametrize("invalid", [np.nan, -1., .5, 65536.])
def test_missing_or_malformed_quality_cannot_enter_calibration(invalid):
    hours = np.arange(0., 24., 3.)
    values = 290 + 8*np.cos(2*np.pi*(hours-15)/24)
    values[0] = 350
    flags = np.zeros(8)
    flags[0] = invalid
    fit = time.fit_diurnal_cycle(values, hours, quality_flag=flags)
    assert fit.sample_count == 7
    assert fit.amplitude_k == pytest.approx(8)
    assert fit.peak_hour == pytest.approx(15)


def test_time_invalid_inputs_do_not_wrap_silently():
    actual = time.normalize_local_solar_time([300, 300, 300], [12, 24, -1], 8, 14)
    assert np.isfinite(actual[0])
    assert np.isnan(actual[1:]).all()
    with pytest.raises(ValueError, match="reference"):
        time.normalize_local_solar_time([300], 12, 8, 14, reference_hour=24)


def scene():
    coarse = np.array([[299., 297., 295.], [293., 291., 289.]])
    x = np.repeat(np.repeat(np.arange(6.).reshape(2, 3), 2, 0), 2, 1)
    x += np.tile([[-.3, -.1], [.1, .3]], (2, 3))
    return coarse, x


def test_downscale_recovers_subpixel_detail_and_coarse_means():
    from base.normalization.downscale import downscale_temperature
    coarse, x = scene()
    result = downscale_temperature(coarse, x)
    np.testing.assert_allclose(result.temperature_k, 299 - 2*x, atol=1e-10)
    np.testing.assert_allclose(result.temperature_k.reshape(2, 2, 3, 2).mean((1, 3)), coarse)
    assert not result.quality_flag.any()
    assert result.training_count == 6


def test_downscale_corrects_nonzero_residual_with_area_weights():
    from base.normalization.downscale import downscale_temperature
    coarse, x = scene()
    coarse[0, 0] += 3
    weights = np.tile([[1., 2.], [1., 2.]], (2, 3))
    result = downscale_temperature(coarse, x, fine_weights=weights)
    actual = (result.temperature_k*weights).reshape(2, 2, 3, 2).sum((1, 3))/6
    np.testing.assert_allclose(actual, coarse, atol=1e-10)
    assert np.max(np.abs(result.coarse_residual_k)) > 0.1


def test_downscale_never_fills_cloud_or_missing_predictors():
    from base.normalization.downscale import downscale_temperature
    coarse, x = scene()
    flags = np.zeros(coarse.shape, dtype=np.uint16)
    flags[0, 0] = QualityFlag.CLOUD
    x[-1, -1] = np.nan
    result = downscale_temperature(coarse, x, coarse_quality_flag=flags)
    assert np.isnan(result.temperature_k[:2, :2]).all()
    assert np.isnan(result.temperature_k[2:, 4:]).all()
    assert (result.quality_flag[:2, :2] & QualityFlag.CLOUD).all()
    assert result.coarse_coverage[-1, -1] == .75
    assert (result.quality_flag[2:, 4:] & QualityFlag.LOW_SUPPORT).all()


def test_downscale_missing_quality_is_not_good():
    from base.normalization.downscale import downscale_temperature
    coarse, x = scene()
    flags = np.zeros(coarse.shape)
    flags[0, 0] = np.nan
    result = downscale_temperature(coarse, x, coarse_quality_flag=flags)
    assert np.isnan(result.temperature_k[:2, :2]).all()
    assert (result.quality_flag[:2, :2] & QualityFlag.INPUT_INVALID).all()


def test_partial_coverage_is_explicit_and_closes_on_valid_pixels():
    from base.normalization.downscale import downscale_temperature
    coarse, x = scene()
    x[-1, -1] = np.nan
    result = downscale_temperature(coarse, x, minimum_coverage=.75)
    assert np.isnan(result.temperature_k[-1, -1])
    assert np.nanmean(result.temperature_k[2:, 4:]) == pytest.approx(coarse[-1, -1])
    assert np.count_nonzero(np.isfinite(result.temperature_k[2:, 4:])) == 3


@pytest.mark.parametrize("kind", ["constant", "shape", "weights", "coverage"])
def test_downscale_rejects_invalid_model_or_grid(kind):
    from base.normalization.downscale import downscale_temperature
    coarse, x = scene()
    kwargs = {}
    if kind == "constant":
        x[:] = 1
    if kind == "shape":
        x = x[:-1]
    if kind == "weights":
        kwargs["fine_weights"] = -np.ones_like(x)
    if kind == "coverage":
        kwargs["minimum_coverage"] = 0
    with pytest.raises(ValueError):
        downscale_temperature(coarse, x, **kwargs)
