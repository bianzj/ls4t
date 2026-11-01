import zipfile

import numpy as np
import pytest

from gui import drivers, layout

SCENE = "S3A_SL_1_RBT____20240715T081014_20240715T081314_20240716T125350_0180_019_249_2879_PS1_O_NT_004.SEN3"


def test_find_sources_prefers_unzipped_folder_and_accepts_layouts(tmp_path):
    (tmp_path / "2024" / "raw").mkdir(parents=True)
    (tmp_path / "2024" / "raw" / (SCENE + ".zip")).write_bytes(b"")
    (tmp_path / "2024" / "raw" / SCENE).mkdir()
    other = SCENE.replace("081014", "091014")
    (tmp_path / "2024" / (other + ".zip")).write_bytes(b"")
    (tmp_path / "2024" / "S3A_SL_2_LST____x.SEN3.zip").write_bytes(b"")

    found = layout.find_sources(tmp_path, "2024")

    assert set(found) == {SCENE, other}
    assert found[SCENE].is_dir()
    assert layout.years(tmp_path) == ["2024"]


def test_flat_folder_scenes_are_grouped_by_start_year(tmp_path):
    (tmp_path / SCENE).mkdir()
    older = SCENE.replace("20240715T081014", "20230328T024339")
    (tmp_path / older).mkdir()
    (tmp_path / "base").mkdir()

    assert layout.years(tmp_path) == ["2024", "2023"]
    assert set(layout.find_sources(tmp_path, "2023")) == {older}


def test_task_inputs_per_kind(tmp_path):
    (tmp_path / "2024").mkdir()
    (tmp_path / "2024" / (SCENE + ".zip")).write_bytes(b"")
    unzipped = SCENE.replace("081014", "091014")
    (tmp_path / "2024" / unzipped).mkdir()
    (tmp_path / "2024" / "lst" / SCENE).mkdir(parents=True)

    assert set(layout.task_inputs("unzip", tmp_path, "2024")) == {SCENE}
    assert set(layout.task_inputs("lst", tmp_path, "2024")) == {SCENE, unzipped}
    assert set(layout.task_inputs("lsct", tmp_path, "2024")) == {SCENE}
    assert layout.task_inputs("lst", tmp_path / "missing", "2024") == {}


@pytest.mark.parametrize(
    "key,dtype,scale",
    [("data", np.float32, 1), ("tcw", np.float32, 1), ("tcwv", np.float64, 1), ("tcw", np.uint16, 100)],
)
def test_tcwv_decoder_handles_local_layouts(tmp_path, key, dtype, scale):
    h5py = pytest.importorskip("h5py")
    cube = np.full((24, 721, 1440), 25.0)  # kg m-2
    cube[5] = 0.0  # a missing hour
    path = tmp_path / "tcwv_20190101.h5"
    with h5py.File(path, "w") as handle:
        handle[key] = (cube * scale).astype(dtype)

    result = drivers.load_tcwv_cm_any(path)

    assert np.allclose(result[0], 2.5)
    assert np.isnan(result[5]).all()


def test_tcwv_decoder_rejects_unknown_units(tmp_path):
    h5py = pytest.importorskip("h5py")
    path = tmp_path / "tcwv_20190101.h5"
    with h5py.File(path, "w") as handle:
        handle["data"] = np.full((24, 721, 1440), 5000.0, np.float32)
    with pytest.raises(ValueError):
        drivers.load_tcwv_cm_any(path)


def test_unzip_extracts_only_wanted_files_flat(tmp_path):
    archive = tmp_path / (SCENE + ".zip")
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(f"{SCENE}/S8_BT_in.nc", b"bt")
        bundle.writestr(f"{SCENE}/flags_io.nc", b"flags")
        bundle.writestr(f"{SCENE}/S7_BT_in.nc", b"unused")
        bundle.writestr("../../evil/flags_in.nc", b"x")
    destination = tmp_path / "out" / SCENE

    status, _ = drivers._unzip_one(archive, destination, overwrite=False)

    assert status == "done"
    assert sorted(p.name for p in destination.iterdir()) == ["S8_BT_in.nc", "flags_in.nc", "flags_io.nc"]
    assert not (tmp_path / "evil").exists()
    assert drivers._unzip_one(archive, destination, overwrite=False)[0] == "skipped"


def test_unzip_rejects_archive_without_thermal_band(tmp_path):
    archive = tmp_path / (SCENE + ".zip")
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(f"{SCENE}/flags_io.nc", b"flags")
    status, _ = drivers._unzip_one(archive, tmp_path / "out" / SCENE, overwrite=False)
    assert status == "failed"
    assert not (tmp_path / "out" / SCENE).exists()


def test_geo_encoding_keeps_negative_coordinates():
    pytest.importorskip("osgeo")
    array, _, nodata = drivers._encode(np.array([[-13.287, 0.5, np.nan]]), "geo")
    assert array.tolist() == [[-1328, 50, nodata]]
    thermal, _, missing = drivers._encode(np.array([[300.123, np.nan]]), "thermal")
    assert thermal.tolist() == [[30012, missing]]
