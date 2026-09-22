"""Structure and dependency checks for the flattened AATSR production case."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases/aatsr"
SCRIPTS = (
    "aatsr_unzip.py",
    "aatsr_data.py",
    "aatsr_lst.py",
    "aatsr_lsct.py",
    "aatsr_lsct_latlon.py",
    "aatsr_lsct_v31.py",
    "aatsr_lsct_ndvi.py",
    "aatsr_001deg_stats.py",
    "aatsr_monthly_3files.py",
    "aatsr_era5_tcw.py",
    "aatsr_site_inv.py",
    "aatsr_site_inv_bayes.py",
    "aatsr_site_validate.py",
    "aatsr_site_series.py",
    "util_aatsr.py",
)


def test_aatsr_case_is_flat_and_base_only():
    if not CASE.is_dir():
        pytest.skip("AATSR execution case is archived")
    for directory in ("support", "implementation", "global"):
        assert not (CASE / directory).exists(), directory
    scripts = sorted(path.name for path in CASE.glob("*.py"))
    assert scripts == sorted(SCRIPTS)
    for name in SCRIPTS:
        source = (CASE / name).read_text(encoding="utf-8")
        assert "cases.support" not in source, name
        assert "import *" not in source, name
        assert "sys.path.append" not in source, name


def test_aatsr_scripts_import_resolvable_names():
    if not CASE.is_dir():
        pytest.skip("AATSR execution case is archived")
    for name in SCRIPTS:
        tree = ast.parse((CASE / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(("base", "aatsr"))
            ):
                module = importlib.import_module(node.module)
                missing = [alias.name for alias in node.names if not hasattr(module, alias.name)]
                assert not missing, f"{name}: {node.module} missing {missing}"


def test_aatsr_helpers_live_in_base_and_aatsr():
    from base.dates import date2DOY, doy2date
    from base.files import read_h5py_items, read_image_Nc, un_gz, write_h5py_item
    from base.fitting import fitting_unknown_linear_ls
    from base.kernel import kernel_LSF
    from base.lsct import cal_psoil_hom, cal_rad_from_lst_fvc
    from base.lsct_window import fitting_Nangle_Mcomponent_window, inv_lsct2_window
    from base.metrics import cal_rmse_r2

    for function in (
        date2DOY,
        doy2date,
        read_h5py_items,
        read_image_Nc,
        un_gz,
        write_h5py_item,
        fitting_unknown_linear_ls,
        kernel_LSF,
        cal_psoil_hom,
        cal_rad_from_lst_fvc,
        fitting_Nangle_Mcomponent_window,
        inv_lsct2_window,
        cal_rmse_r2,
    ):
        assert callable(function), function
    if CASE.is_dir():
        from cases.aatsr.util_aatsr import aatsr_read_angle, aatsr_read_clo, aatsr_read_lst

        for function in (aatsr_read_angle, aatsr_read_clo, aatsr_read_lst):
            assert callable(function), function


def test_aatsr_moved_helpers_keep_their_numbers():
    from base.dates import date2DOY, doy2date
    from base.kernel import kernel_LSF, kernel_RLf
    from base.metrics import cal_rmse_r2

    assert date2DOY(2005, 8, 1) == 213
    assert doy2date(2005, 213) == (8, 1)
    vza = np.deg2rad(np.array([0.0, 30.0, 60.0]))
    assert np.allclose(
        kernel_LSF(vza),
        np.asarray([1.030367254714, 1.030370437051, 1.030379984814]),
        rtol=0,
        atol=1e-12,
    )
    assert np.isclose(kernel_RLf(np.deg2rad(30.0), np.deg2rad(40.0), 0.0), 0.0030465228390619066)
    bias, rmse, r2 = cal_rmse_r2(np.array([1.0, 2.0, 3.0]), np.array([1.1, 1.9, 3.2]))
    assert np.isclose(bias, 0.06666666666666672)
    assert np.isclose(rmse, 0.14142135623730964)
    assert np.isclose(float(np.asarray(r2).max()), 1.0)
