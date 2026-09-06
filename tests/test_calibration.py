from pathlib import Path

import numpy as np

from base.calibration import legacy_split_window_model, load_split_window_model, save_split_window_model


def test_legacy_coefficient_table_round_trip(tmp_path: Path):
    vza = np.array([0.0, 60.0])
    water = np.array([0.0, 2.0, 5.0])
    table = np.arange(4 * 10, dtype=float).reshape(4, 10)
    model = legacy_split_window_model(table, vza, water, coefficient_columns=slice(2, 10))
    np.testing.assert_array_equal(model.coefficients[1, 0], table[2, 2:10])
    path = tmp_path / "coefficients.npz"
    save_split_window_model(path, model, sensor="AATSR", version="1")
    restored = load_split_window_model(path)
    np.testing.assert_array_equal(restored.coefficients, model.coefficients)
