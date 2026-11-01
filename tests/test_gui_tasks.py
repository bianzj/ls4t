import json
import sys
from pathlib import Path

import pytest

GUI = Path(__file__).resolve().parents[1] / "gui"
sys.path.insert(0, str(GUI))

import tasks  # noqa: E402

SCENE = "S3A_SL_1_RBT____20230328T024339_20230328T024639_20230329T173806_0180_097_089_2340_PS1_O_NT_004.SEN3"


@pytest.fixture(autouse=True)
def task_file(tmp_path, monkeypatch):
    path = tmp_path / "tasks.json"
    monkeypatch.setattr(tasks, "TASKS_FILE", path)
    return path


def _raster(path, width, height):
    gdal = pytest.importorskip("osgeo.gdal")
    gdal.UseExceptions()
    gdal.GetDriverByName("GTiff").Create(str(path), width, height, 1, gdal.GDT_Int16, options=["SPARSE_OK=TRUE", "TILED=YES"])


def _data(tmp_path, kind="lst", global_grid=True):
    zips = tmp_path / "zips"
    (zips / "2023").mkdir(parents=True)
    (zips / "2023" / (SCENE + ".zip")).write_bytes(b"")
    (zips / "2024").mkdir()
    lst_out = tmp_path / "lst_out"
    (lst_out / "2023" / "lst" / SCENE).mkdir(parents=True)
    lai = tmp_path / "lai"
    (lai / "lai_2021-2025_0p01deg" / "2023").mkdir(parents=True)
    (lai / "lai_2021-2025_0p01deg" / "2023" / "LAI_2023001.h5").write_bytes(b"")
    tcwv = tmp_path / "tcwv"
    (tcwv / "2023").mkdir(parents=True)
    (tcwv / "2023" / "tcwv_20230101.h5").write_bytes(b"")
    aux = tmp_path / "aux"
    aux.mkdir()
    (aux / "IGBP_Emi.txt").write_text("0 0\n")
    (aux / "Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt").write_text("0\n")
    width, height = (36000, 18000) if global_grid else (100, 50)
    for name in ("AG1km.v003.SoilEmi.ABI.Global.001D_LSE11.tif", "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif",
                 "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif"):
        _raster(aux / name, width, height)
    _raster(tmp_path / "type.tif", width, height)
    return {
        "type": kind,
        "name": f"北京 2023 {kind}",
        "input_dir": str(lst_out if kind == "lsct" else zips),
        "output_dir": str(tmp_path / "out"),
        "years": ["2023"],
        "lai_root": str(lai),
        "tcwv_root": str(tcwv),
        "aux_dir": str(aux),
        "soil_emis_b1": str(aux / "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif"),
        "soil_emis_b2": str(aux / "AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif"),
        "type_map": str(tmp_path / "type.tif"),
    }


@pytest.mark.parametrize("kind", ["unzip", "lst", "lsct"])
def test_check_accepts_complete_task_of_each_kind(tmp_path, kind):
    result = tasks.check(_data(tmp_path, kind))
    assert result["ok"], {k: v for k, v in result["fields"].items() if not v["ok"]}
    assert result["years_available"] == [{"year": "2023", "scenes": 1}]
    expected = {"unzip": set(), "lst": {"lai_root", "tcwv_root", "aux_dir"}, "lsct": {"lai_root", "aux_dir"}}[kind]
    assert expected <= set(result["fields"])
    assert "tcwv_root" not in result["fields"] or kind == "lst"


def test_check_suggests_modis_bands(tmp_path):
    values = dict(_data(tmp_path), soil_emis_b1="", soil_emis_b2="")
    result = tasks.check(values)
    assert Path(result["suggest"]["soil_emis_b1"]).name.endswith("MODIS.Global.001D_LSE11.tif")
    assert Path(result["suggest"]["soil_emis_b2"]).name.endswith("MODIS.Global.001D_LSE12.tif")
    assert len(result["emissivity"]) == 3


def test_check_reports_missing_drivers_wrong_grid_and_absent_year(tmp_path):
    values = _data(tmp_path, global_grid=False)
    values["years"] = ["2023", "2024"]
    values["soil_emis_b2"] = values["soil_emis_b1"]
    fields = tasks.check(values)["fields"]
    assert "2024 年没有 LAI" in fields["years"]["message"]
    assert "输入目录里没有 2024 年的数据" in fields["years"]["message"]
    assert "36000×18000" in fields["soil_emis_b1"]["message"]
    assert fields["soil_emis_b2"]["message"] == "两个波段选了同一个文件"


def test_save_update_delete_and_record_run(tmp_path, task_file):
    values = _data(tmp_path)
    task = tasks.save(values)
    assert [t["id"] for t in tasks.all_tasks()] == [task["id"]]
    with pytest.raises(ValueError):
        tasks.save(dict(values, name=""))
    updated = tasks.save(dict(values, name="北京"), task["id"])
    assert updated["name"] == "北京" and len(tasks.all_tasks()) == 1
    tasks.record_run(task["id"], {"state": "done", "counts": {"done": 1, "skipped": 0, "failed": 0}})
    assert tasks.get(task["id"])["last_run"]["state"] == "done"
    assert tasks.template("lsct")["aux_dir"] == values["aux_dir"]
    tasks.delete(task["id"])
    assert tasks.all_tasks() == [] and json.loads(task_file.read_text(encoding="utf-8")) == {"tasks": []}
    assert Path(values["input_dir"]).is_dir()  # deleting a task never touches data
