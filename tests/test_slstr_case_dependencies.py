"""Regression checks for the helpers the SLSTR cases import from base/.

The expected values were produced by the original run-project implementation
before the code moved into base, so these tests keep the production numbers
stable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from base.dates import date2DOY
from base.lsct import (
    cal_fvc_from_lai,
    cal_rad_from_lst,
)
from base.radiometry import inv_planck, planck
from base.rt.gap import gap_probability_hom_analytical
from base.rt.hom import Hom
from base.rt.hotspot import hotspot_layer
from base.slstr import slstr_grid


LAI = np.array([0.5, 1.5, 3.0, 5.0])
VZA = np.deg2rad(np.array([10.0, 25.0, 40.0, 55.0]))
SZA = np.deg2rad(np.array([25.0, 30.0, 35.0, 40.0]))
VAA = np.deg2rad(np.array([20.0, 25.0, 30.0, 35.0]))
LST = np.array([290.0, 295.0, 300.0, 305.0])


def test_slstr_grid_constants():
    assert (
        slstr_grid.nl_nadir_g,
        slstr_grid.ns_nadir_g,
        slstr_grid.nl_obliq_g,
        slstr_grid.ns_obliq_g,
        slstr_grid.nl_nadir_v_g,
        slstr_grid.ns_nadir_v_g,
    ) == (1200, 1500, 1200, 900, 2400, 3000)
    assert (
        slstr_grid.adjust_xmin_n_g,
        slstr_grid.adjust_xmax_n_g,
        slstr_grid.adjust_xmin_no_g,
        slstr_grid.adjust_xmax_no_g,
        slstr_grid.adjust_ymax_no_g,
        slstr_grid.adjust_xmin_o_g,
        slstr_grid.adjust_xmax_o_g,
    ) == (0, 96, 548, 1448, 1200, 36, 95)


def test_date2doy():
    assert date2DOY(2020, 1, 1) == 1
    assert date2DOY(2020, 12, 31) == 366
    assert date2DOY(2021, 3, 1) == 60


def test_planck_and_inverse_round_trip():
    radiance = planck(10.8, LST.copy())
    assert np.allclose(radiance, [8.281149, 8.95913, 9.667849, 10.407299], atol=1e-6)
    assert np.allclose(inv_planck(10.8, radiance.copy()), LST, atol=1e-6)


def test_vegetation_fraction_from_lai_matches_run_project():
    fvc = cal_fvc_from_lai(VZA, LAI)
    assert np.allclose(
        fvc, [0.2212, 0.527644, 0.776895, 0.917944], atol=1e-6
    )
    assert np.all((fvc >= 0) & (fvc <= 1))


def test_gap_probability_matches_run_project():
    gap = gap_probability_hom_analytical(LAI, VZA)
    assert np.allclose(gap, [0.7788, 0.472356, 0.223105, 0.082056], atol=1e-6)
    assert np.all(np.diff(gap) < 0)


def test_hotspot_layer_matches_run_project():
    hotspot = hotspot_layer(LAI, 0.2, VZA, SZA, VAA)
    assert np.allclose(
        hotspot, [0.778798, 0.472354, 0.223108, 0.082063], atol=1e-6
    )


def test_component_radiance_matches_run_project():
    radiance = cal_rad_from_lst(
        np.array([290.0, 300.0, 310.0]), 10.8, 2.0, np.deg2rad(30.0), 0.95, 0.98
    )
    assert np.allclose(radiance, [8.136089, 9.498498, 10.981642], atol=1e-6)


def test_homogeneous_canopy_emissivity_matches_run_project():
    model = Hom()
    model.set_thermal(LST, LST, LST + 1, LST + 1)
    model.set_structure(LAI, 0.2)
    model.set_optical(10.8, 0.95, 0.98)
    model.set_angle(VZA, SZA, np.deg2rad(np.zeros(4)))
    expected = np.array(
        [
            [0.739858, 0.448736, 0.211953, 0.07796],
            [2e-06, 2e-06, 0.0, 0.0],
            [0.228324, 0.531603, 0.769133, 0.896316],
            [0.002845, 0.008268, 0.012866, 0.020009],
        ]
    )
    assert np.allclose(model.run_emis(), expected, atol=1e-6)


def test_resize_data_matches_run_project():
    cv2 = pytest.importorskip("cv2")
    from base.spatial import resize_data

    rng = np.random.default_rng(20260916)
    source = rng.random((37, 53))
    expected = cv2.resize(source.copy(), (30, 20), interpolation=0)
    assert np.array_equal(resize_data(source.copy(), 20, 30), expected)


def test_slstr_cases_are_flat_and_depend_on_base_only():
    root = Path(__file__).resolve().parents[1] / "cases/slstr"
    if not root.is_dir():
        pytest.skip("SLSTR execution case is archived")
    for directory in ("support", "implementation", "batch", "auxiliary", "regions"):
        assert not (root / directory).exists(), directory
    scripts = sorted(root.glob("*.py"))
    assert scripts
    for script in scripts:
        source = script.read_text(encoding="utf-8")
        assert "cases.slstr.support" not in source, script.name
        assert "import *" not in source, script.name
        assert "sys.path.append" not in source, script.name


def test_window_component_retrieval_matches_aatrs_history():
    """Golden values from the AATSR implementation restored into base."""
    from base.lsct import inv_lsct2_window, inv_lsct3_window

    rng = np.random.default_rng(7)
    nl = ns = 9
    n, m, ws, wl = 2, 2, 5, 10.8
    w = np.full((nl, ns, n, m), 0.97) + rng.normal(0, 0.005, (nl, ns, n, m))
    brightness = 300.0 + rng.normal(0, 0.5, (nl, ns, n))
    mask = np.ones((nl, ns, n))
    lst = 300.0 + rng.normal(0, 1.0, (nl, ns, n))
    with np.errstate(divide="ignore", invalid="ignore"):
        lsct2 = inv_lsct2_window(n, m, ws, wl, w, brightness, mask, lst)
        three = 3
        w3 = np.full((nl, ns, n, three), 0.97) + rng.normal(0, 0.005, (nl, ns, n, three))
        lsct3 = inv_lsct3_window(n, three, ws, wl, w3, brightness, mask, lst)
    assert lsct2.shape == (nl, ns, m)
    assert lsct3.shape == (nl, ns, three)
    # SLSQP stops on the constraint boundary within its own tolerance; SciPy >= 1.16 lands ~5 mK away.
    assert np.allclose(lsct2[4, 4], [327.547852, 300.537886], atol=1e-2)
    assert np.allclose(
        lsct3[4, 4], [335.508742, 300.537886, 314.728371], atol=1e-2
    )
    assert np.isfinite(lsct2[2:-2, 2:-2]).all()
    assert np.isfinite(lsct3[2:-2, 2:-2]).all()
