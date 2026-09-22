"""Structure and dependency checks for the flattened MSG production case."""

from __future__ import annotations

import ast
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
    "msg_project_iodc.py",
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
    "msg_lsct_2c_full.py",
    "msg_lsct_3c_2stage_full.py",
    "msg_lsct_3c_full.py",
    "msg_lsct_3c_constrained_full.py",
    "msg_lsct_3c_show_full.py",
)


def test_msg_case_is_flat_and_base_only():
    if not CASE.is_dir():
        pytest.skip("MSG execution case is archived")
    for directory in ("support", "implementation", "ingest", "europe_africa"):
        assert not (CASE / directory).exists(), directory
    scripts = sorted(path.name for path in CASE.glob("*.py"))
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
