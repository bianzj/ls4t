import numpy as np
import pytest

from base.quality import QualityFlag
from normalization.angle import normalize_directional
from normalization.fusion import NormalizedField, fuse_l3n
from normalization.profile import NormalizationProfile
from normalization.sensor import SensorHarmonization
from normalization.space import aggregate_to_grid, space_normalize_years
from normalization.time import normalize_local_solar_time


def profile(name="OPS"):
    return NormalizationProfile(name, "1", "GLOBAL-001", "daily")


def normalized(sensor, value, uncertainty=1.0, selected_profile=None):
    values = np.asarray(value, dtype=float)
    return NormalizedField(
        sensor,
        values,
        np.broadcast_to(np.asarray(uncertainty, dtype=float), values.shape).copy(),
        np.zeros(values.shape, dtype=np.uint16),
        selected_profile or profile(),
    )


def test_angle_time_and_sensor_are_independent_operations():
    temperature = normalize_directional(
        np.array([300.0]),
        np.array([0.0]),
        np.array([30.0]),
        np.array([0.0]),
        np.zeros((1, 3)),
    )
    temperature = normalize_local_solar_time(
        temperature,
        np.array([10.0]),
        np.array([10.0]),
        np.array([14.0]),
        reference_hour=14.0,
    )
    model = SensorHarmonization("AATSR", "SLSTR", offset_k=1.0, calibration_uncertainty_k=0.5)
    temperature, uncertainty = model.apply(temperature, np.array([1.0]))
    np.testing.assert_allclose(temperature, [306.0])
    np.testing.assert_allclose(uncertainty, [np.sqrt(1.25)])


def test_compatible_l3n_fusion_keeps_l3n_semantics():
    result = fuse_l3n([normalized("AATSR", [300.0]), normalized("SLSTR", [302.0])])
    np.testing.assert_allclose(result.temperature_k, [301.0])
    np.testing.assert_allclose(result.uncertainty_k, [np.sqrt(0.5)])
    assert result.contributing_sensors[0] == 2


def test_fusion_rejects_profile_mismatch():
    first = normalized("AATSR", [300.0])
    second = normalized("SLSTR", [301.0], selected_profile=profile("OTHER"))
    with pytest.raises(ValueError, match="incompatible"):
        fuse_l3n([first, second])


def test_grid_aggregation_counts_duplicates():
    output, support = aggregate_to_grid(
        np.array([300.0, 304.0, 310.0]),
        np.array([0, 0, 1]),
        np.array([0, 0, 1]),
        (2, 2),
    )
    assert output[0, 0] == 302.0
    assert support[0, 0] == 2.0
    assert output[1, 1] == 310.0


def test_grid_aggregation_reports_outside_samples():
    with pytest.raises(IndexError, match="outside"):
        aggregate_to_grid(np.array([300.0]), np.array([2]), np.array([0]), (2, 2))


def test_space_normalization_excludes_flagged_samples(tmp_path):
    input_path = tmp_path / "input" / "2026" / "scene.npz"
    input_path.parent.mkdir(parents=True)
    np.savez(
        input_path,
        temperature_k=np.array([300.0, 310.0]),
        uncertainty_k=np.array([1.0, 1.0]),
        quality_flag=np.array([QualityFlag.CLOUD, 0], dtype=np.uint16),
        target_row_index=np.array([0, 0]),
        target_column_index=np.array([0, 0]),
    )
    space_normalize_years(
        indir_time=tmp_path / "input",
        outdir_space=tmp_path / "output",
        years=[2026],
        target_shape=(1, 1),
    )
    with np.load(tmp_path / "output" / "2026" / "scene.npz") as result:
        assert result["temperature_k"].item() == 310.0
        assert result["quality_flag"].item() == 0
