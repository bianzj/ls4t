"""Structure and dependency checks for the flattened MSG production case."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import importlib
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases/msg"
SCRIPTS = (
    "msg_download.py",
    "msg_extract_euro.py",
    "msg_extract_iodc.py",
    "msg_project_euro.py",
    "msg_project_euro_lai.py",
    "msg_project_hdf5.py",
    "msg_project_iodc.py",
    "msg_smoke_test.py",
    "msg_lst_fit.py",
    "msg_lsct_iter.py",
    "msg_site_extract_lst.py",
    "msg_site_extract_lai.py",
    "msg_site_extract_static.py",
    "msg_site_extract_csv.py",
    "msg_site_fit.py",
    "msg_site_validate.py",
    "msg_site_stats.py",
    "msg_site_extract_series.py",
    "msg_site_repro_lst.py",
    "msg_site_repro_lsct.py",
    "msg_site_validate_multisite.py",
    "experiments/msg_lsct_2c_window.py",
    "experiments/msg_lsct_3c_two_stage.py",
    "experiments/msg_lsct_3c_window.py",
    "experiments/msg_lsct_3c_constrained.py",
    "experiments/msg_lsct_3c_diagnostics.py",
)


def test_msg_case_is_flat_and_base_only():
    if not CASE.is_dir():
        pytest.skip("MSG execution case is archived")
    for directory in ("support", "implementation", "ingest", "europe_africa"):
        assert not (CASE / directory).exists(), directory
    scripts = sorted(path.relative_to(CASE).as_posix() for path in CASE.rglob("*.py"))
    assert scripts == sorted(SCRIPTS)
    for name in SCRIPTS:
        source = (CASE / name).read_text(encoding="utf-8")
        assert "cases.support" not in source, name
        assert "import *" not in source, name
        assert "sys.path.append" not in source, name


def test_msg_scripts_import_resolvable_base_names():
    if not CASE.is_dir():
        pytest.skip("MSG execution case is archived")
    for name in SCRIPTS:
        tree = ast.parse((CASE / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(("base", "slstr"))
            ):
                module = importlib.import_module(node.module)
                missing = [alias.name for alias in node.names if not hasattr(module, alias.name)]
                assert not missing, f"{name}: {node.module} missing {missing}"


def test_msg_dependencies_live_in_base():
    from base.dates import date2DOY
    from base.files import (
        mkdir_if_not_exist,
        read_image_gdal,
        read_image_dataset_gdal,
        read_txt_array,
        search_file,
    )
    from base.lsct import ndvi_max_g, ndvi_min_g
    from base.radiometry import inv_planck, planck
    from base.rt.gap import gap_probability_hom_analytical
    from base.spatial import loc2map, resize_data

    for function in (
        date2DOY,
        mkdir_if_not_exist,
        read_image_gdal,
        read_image_dataset_gdal,
        read_txt_array,
        search_file,
        loc2map,
        resize_data,
        planck,
        inv_planck,
        gap_probability_hom_analytical,
    ):
        assert callable(function), function
    assert ndvi_min_g < ndvi_max_g


def test_search_file_matches_msg_case_semantics(tmp_path):
    from base.files import search_file

    for name in ("a.zip", "b.zip", "a_aux.zip", "c.txt"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()

    assert sorted(search_file(str(tmp_path), [".zip"])) == [
        "a.zip",
        "a_aux.zip",
        "b.zip",
    ]
    assert search_file(str(tmp_path), [".zip", "aux"]) == ["a_aux.zip"]
    assert search_file(str(tmp_path), [".zip", "aux", "a_"]) == ["a_aux.zip"]
    assert sorted(search_file(str(tmp_path), [])) == [
        "a.zip",
        "a_aux.zip",
        "b.zip",
        "c.txt",
        "sub",
    ]


def test_resize_data_available_for_msg_grids():
    import pytest

    pytest.importorskip("cv2")
    from base.spatial import resize_data

    source = np.arange(20.0).reshape(4, 5)
    resized = resize_data(source.copy(), 8, 10)
    assert resized.shape == (8, 10)


def test_msg_projection_profiles_use_mounted_disk_layout():
    from cases.msg.msg_project_hdf5 import PRODUCTS, parse_hours

    assert PRODUCTS["euro-lst"].input_relative == "PRODUCTS/MSG/MLST/HDF5"
    assert PRODUCTS["iodc-lst"].input_relative == "PRODUCTS/MSG-IODC/MLST/HDF5"
    assert PRODUCTS["euro-lai"].variable == "LAI"
    assert parse_hours("0,9,16") == {0, 9, 16}


def test_active_msg_projection_scripts_have_no_legacy_machine_paths():
    for name in (
        "msg_project_hdf5.py",
        "msg_project_euro.py",
        "msg_project_euro_lai.py",
        "msg_project_iodc.py",
        "msg_lst_fit.py",
        "msg_lsct_iter.py",
        "msg_smoke_test.py",
    ):
        source = (CASE / name).read_text(encoding="utf-8")
        assert "/mnt/h/" not in source, name
        assert "/Users/" not in source, name


def test_msg_lst_uses_scaled_global_tcwv(tmp_path):
    import h5py

    from cases.msg.msg_lst_fit import load_tcwv_slice

    tcwv_root = tmp_path / "tcwv" / "2017"
    tcwv_root.mkdir(parents=True)
    with h5py.File(tcwv_root / "tcwv_20170803.h5", "w") as handle:
        field = handle.create_dataset("data", data=np.full((24, 2, 3), 2500, dtype=np.uint16))
        field.attrs["scale_factor"] = 0.01
        field.attrs["_FillValue"] = 65535

    result = load_tcwv_slice(tmp_path / "tcwv", datetime(2017, 8, 3, 9, tzinfo=timezone.utc))
    assert np.allclose(result, 2.5)


def test_msg_lst_selects_day_and_night_coefficients():
    from cases.msg.msg_lst_fit import retrieve_lst

    shape = (1, 2)
    day_coefficients = np.zeros((66, 8), dtype=np.float32)
    night_coefficients = np.zeros((66, 8), dtype=np.float32)
    day_coefficients[:, 1] = 1.0
    night_coefficients[:, 1] = 1.0
    night_coefficients[:, 0] = 5.0
    result = retrieve_lst(
        np.full(shape, 300.0),
        np.full(shape, 300.0),
        np.full(shape, 10.0),
        np.full(shape, 2.0),
        np.full(shape, 0.98),
        np.full(shape, 0.98),
        np.full(shape, 0.98),
        np.full(shape, 0.98),
        np.full(shape, 1.0),
        np.ones(shape, dtype=bool),
        np.asarray([[True, False]]),
        day_coefficients,
        night_coefficients,
    )
    assert np.allclose(result, [[300.0, 305.0]])
