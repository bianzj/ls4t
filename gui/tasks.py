"""Processing tasks: unzip, LST retrieval and LSCT retrieval, each with an input and an output folder.

Task definitions live in gui/tasks.json (not versioned). Deleting a task only removes it
from the list; no data is touched.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path

import layout

GUI_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ["LS4T_STATE_DIR"]) if os.environ.get("LS4T_STATE_DIR") else GUI_DIR
TASKS_FILE = STATE_DIR / "tasks.json"
GLOBAL_SHAPE = (18000, 36000)  # 0.01 degree global grid used by the production code
LAI_FOLDERS = ("lai_2002-2020_0p01deg", "lai_2021-2025_0p01deg")
IGBP_TABLE = "IGBP_Emi.txt"
SW_COEFFICIENTS = "Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt"
_LOCK = threading.Lock()  # runs finish on a background thread while the page may save

TYPES = {
    "unzip": {
        "name": "解压",
        "summary": "从 .SEN3.zip 中取出后续需要的 19 个 NetCDF 文件。",
        "input": "zip 目录",
        "input_hint": "SL_1_RBT 的 .SEN3.zip，一般按年份分目录（zip 目录/2023/…），也可以平铺。",
        "output_hint": "结果写到 输出目录/年份/raw/<场景>.SEN3/。",
        "fields": ["years", "overwrite"],
    },
    "lst": {
        "name": "LST 反演",
        "summary": "重整为条带 GeoTIFF 并用生产分裂窗算法反演地表温度。",
        "input": "解压数据目录",
        "input_hint": "解压后的 .SEN3 目录（解压任务的输出目录，或已解压的原始数据），按年份存放或平铺；如果给的是 zip 目录，会先解压到输出目录。",
        "output_hint": "重整结果写到 输出目录/年份/tif/，LST 写到 输出目录/年份/lst/<场景>/lst_nadir.tif、lst_obliq.tif。",
        "fields": ["years", "lai_root", "tcwv_root", "aux_dir", "soil_emis_b1", "soil_emis_b2", "type_map", "include_night", "overwrite"],
    },
    "lsct": {
        "name": "LSCT 反演",
        "summary": "用天底和后向两个视角的 LST 分解土壤与植被组分温度。",
        "input": "LST 结果目录",
        "input_hint": "LST 反演任务的输出目录（需要其中的 年份/tif 与 年份/lst）。",
        "output_hint": "结果写到 输出目录/年份/lsct/<场景>/lsct2.tif（波段 1 土壤，波段 2 植被，K）。",
        "fields": ["years", "lai_root", "aux_dir", "soil_emis_b1", "soil_emis_b2", "type_map", "include_night", "overwrite"],
    },
}

LABELS = {
    "name": "任务名称",
    "input_dir": "输入目录",
    "output_dir": "输出目录",
    "years": "处理年份",
    "lai_root": "LAI 目录",
    "tcwv_root": "TCWV 目录",
    "aux_dir": "辅助数据目录",
    "soil_emis_b1": "土壤发射率 波段 1",
    "soil_emis_b2": "土壤发射率 波段 2",
    "type_map": "IGBP 类型图",
    "include_night": "处理夜间场景",
    "overwrite": "覆盖已有结果",
}

SHARED = ("lai_root", "tcwv_root", "aux_dir", "soil_emis_b1", "soil_emis_b2", "type_map")

TEMPLATE = {
    "type": "lst",
    "name": "",
    "input_dir": "",
    "output_dir": "",
    "years": [],
    "lai_root": r"E:\remote-sensing\vegetation-structure-state\MUSYQ-LAI\standardized",
    "tcwv_root": r"H:\data\rs\tcwv",
    "aux_dir": r"E:\remote-sensing\temperature-emissivity\emissivity",
    "soil_emis_b1": r"E:\remote-sensing\temperature-emissivity\emissivity\AG1km.v003.SoilEmi.MODIS.Global.001D_LSE11.tif",
    "soil_emis_b2": r"E:\remote-sensing\temperature-emissivity\emissivity\AG1km.v003.SoilEmi.MODIS.Global.001D_LSE12.tif",
    "type_map": r"E:\remote-sensing\land-cover-geography\land-cover\type-maps\type_world_1000.tif",
    "include_night": False,
    "overwrite": False,
}


# ------------------------------------------------------------------------ storage


def _read() -> list[dict]:
    if not TASKS_FILE.is_file():
        return []
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8")).get("tasks", [])
    except (OSError, ValueError):
        return []


def _write(items: list[dict]) -> None:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = TASKS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"tasks": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, TASKS_FILE)


def all_tasks() -> list[dict]:
    return [dict(TEMPLATE, **t) for t in _read()]


def get(identifier: str) -> dict:
    for task in all_tasks():
        if task["id"] == identifier:
            return task
    raise FileNotFoundError("任务不存在")


def template(kind: str) -> dict:
    """Defaults for a new task; global data locations follow the most recent task."""
    task = dict(TEMPLATE, type=kind if kind in TYPES else "lst")
    existing = all_tasks()
    if existing:
        latest = existing[-1]
        for key in SHARED:
            if latest.get(key):
                task[key] = latest[key]
    return task


def normalize(values: dict) -> dict:
    task = dict(TEMPLATE)
    task["type"] = values.get("type") if values.get("type") in TYPES else "lst"
    for key, default in TEMPLATE.items():
        if key in ("type",) or key not in values:
            continue
        if key == "years":
            task["years"] = sorted({str(y) for y in values.get("years") or [] if re.fullmatch(r"\d{4}", str(y))})
        elif isinstance(default, bool):
            task[key] = bool(values[key])
        else:
            task[key] = str(values[key] or "").strip().strip('"')
    return task


def save(values: dict, identifier: str | None = None) -> dict:
    task = normalize(values)
    if not task["name"]:
        raise ValueError("请填写任务名称")
    if not task["input_dir"] or not task["output_dir"]:
        raise ValueError("请选择输入目录和输出目录")
    task["input_dir"] = os.path.abspath(task["input_dir"])
    task["output_dir"] = os.path.abspath(task["output_dir"])
    with _LOCK:
        identifier = _store(task, identifier)
    return get(identifier)


def _store(task: dict, identifier: str | None) -> str:
    items = _read()
    if identifier:
        for index, item in enumerate(items):
            if item["id"] == identifier:
                items[index] = dict(item, **task)
                break
        else:
            raise FileNotFoundError("任务不存在")
    else:
        identifier = uuid.uuid4().hex[:10]
        items.append(dict(task, id=identifier, created=time.strftime("%Y-%m-%d %H:%M:%S")))
    _write(items)
    return identifier


def delete(identifier: str) -> None:
    with _LOCK:
        _write([t for t in _read() if t["id"] != identifier])


def record_run(identifier: str, run: dict) -> None:
    with _LOCK:
        items = _read()
        for item in items:
            if item["id"] == identifier:
                item["last_run"] = run
        _write(items)


# ------------------------------------------------------------------ scene inputs


def inputs(task: dict, year: str) -> dict[str, Path]:
    """Scenes of one year that this task would process: {scene name: source path}."""
    return layout.task_inputs(task["type"], task["input_dir"], year)


def input_years(task: dict) -> list[dict]:
    root = Path(task["input_dir"])
    if not root.is_dir():
        return []
    if task["type"] == "lsct":
        candidates = [p.name for p in root.iterdir() if p.is_dir() and re.fullmatch(r"(19|20)\d\d", p.name)]
    else:
        candidates = layout.years(root)
    result = []
    for year in sorted(candidates, reverse=True):
        count = len(inputs(task, year))
        if count:
            result.append({"year": year, "scenes": count})
    return result


# ----------------------------------------------------------------------- checking


def _raster_shape(path: str) -> tuple[int, int] | None:
    import gdal_env  # noqa: F401  (makes GDAL loadable in an un-activated conda env)
    from osgeo import gdal

    gdal.UseExceptions()
    try:
        dataset = gdal.Open(path)
        return dataset.RasterYSize, dataset.RasterXSize
    except RuntimeError:
        return None


def find_aux(folder: Path, name: str) -> Path | None:
    for candidate in (folder / name, folder / "emis" / name, folder / "type" / name, folder / "base" / name):
        if candidate.is_file():
            return candidate
    return None


def emissivity_candidates(aux_dir: str) -> list[str]:
    folder = Path(aux_dir)
    files = []
    for sub in (folder, folder / "emis"):
        if sub.is_dir():
            files += [str(p) for p in sorted(sub.glob("*.tif"))]
    return files


def _guess_band(candidates: list[str], band: str) -> str:
    """MODIS LSE11/LSE12 are the bands the production runs use."""
    for path in candidates:
        if "MODIS" in Path(path).name and Path(path).stem.endswith(band):
            return path
    for path in candidates:
        if Path(path).stem.endswith(band):
            return path
    return ""


def lai_year(lai_root: Path, year: str) -> bool:
    for folder in (lai_root / year, *(lai_root / f / year for f in LAI_FOLDERS)):
        if folder.is_dir() and any(folder.glob("*.h5")):
            return True
    return False


def check(values: dict) -> dict:
    """Field-by-field status of a task definition, plus choices for the form."""
    task = normalize(values)
    kind = TYPES[task["type"]]
    result: dict = {"fields": {}, "years_available": [], "years": {}, "emissivity": [], "suggest": {}}
    fields = result["fields"]

    def put(key, ok, message=""):
        fields[key] = {"label": LABELS[key], "ok": bool(ok), "message": message}

    put("name", task["name"], "" if task["name"] else "必填")

    root = Path(task["input_dir"]) if task["input_dir"] else None
    if root and root.is_dir():
        available = input_years(task)
        result["years_available"] = available
        empty = {"unzip": "没有找到 .SEN3.zip", "lst": "没有找到 SL_1_RBT 产品", "lsct": "没有找到 年份/lst 下的 LST 结果"}
        put("input_dir", bool(available), "" if available else empty[task["type"]])
    else:
        put("input_dir", False, "目录不存在" if task["input_dir"] else "必填")

    out = Path(task["output_dir"]) if task["output_dir"] else None
    if out is None:
        put("output_dir", False, "必填")
    elif out.is_dir():
        put("output_dir", True, "已存在；已有结果的场景会跳过" if not task["overwrite"] else "已存在；已有结果会被覆盖")
    else:
        put("output_dir", bool(out.anchor) and Path(out.anchor).exists(), "运行时创建")

    lai_root = Path(task["lai_root"]) if task["lai_root"] else None
    tcwv_root = Path(task["tcwv_root"]) if task["tcwv_root"] else None
    if "lai_root" in kind["fields"]:
        put("lai_root", lai_root and lai_root.is_dir(), "" if lai_root and lai_root.is_dir() else "目录不存在")
    if "tcwv_root" in kind["fields"]:
        put("tcwv_root", tcwv_root and tcwv_root.is_dir(), "" if tcwv_root and tcwv_root.is_dir() else "目录不存在")

    problems = []
    for year in task["years"]:
        flags = {}
        if "lai_root" in kind["fields"]:
            flags["lai"] = bool(lai_root and lai_root.is_dir() and lai_year(lai_root, year))
            if not flags["lai"]:
                problems.append(f"{year} 年没有 LAI")
        if "tcwv_root" in kind["fields"]:
            flags["tcwv"] = bool(tcwv_root and (tcwv_root / year).is_dir() and any((tcwv_root / year).glob("tcwv_*.h5")))
            if not flags["tcwv"]:
                problems.append(f"{year} 年没有 TCWV")
        result["years"][year] = flags
    available_years = {y["year"] for y in result["years_available"]}
    missing = [y for y in task["years"] if root and root.is_dir() and y not in available_years]
    problems += [f"输入目录里没有 {y} 年的数据" for y in missing]
    put("years", task["years"] and not problems, "必须至少选一年" if not task["years"] else "；".join(problems))

    if "aux_dir" in kind["fields"]:
        aux = Path(task["aux_dir"]) if task["aux_dir"] else None
        if aux and aux.is_dir():
            needed = [IGBP_TABLE] + ([SW_COEFFICIENTS] if task["type"] == "lst" else [])
            lacking = [n for n in needed if find_aux(aux, n) is None]
            put("aux_dir", not lacking, "缺少 " + "、".join(lacking) if lacking else "已找到 " + "、".join(needed))
            candidates = emissivity_candidates(str(aux))
            result["emissivity"] = candidates
            result["suggest"] = {"soil_emis_b1": _guess_band(candidates, "LSE11"), "soil_emis_b2": _guess_band(candidates, "LSE12")}
        else:
            put("aux_dir", False, "目录不存在" if task["aux_dir"] else "必填")
        for key in ("soil_emis_b1", "soil_emis_b2", "type_map"):
            value = task[key]
            if not value:
                put(key, False, "必选")
            elif not Path(value).is_file():
                put(key, False, "文件不存在")
            else:
                shape = _raster_shape(value)
                if shape != GLOBAL_SHAPE:
                    put(key, False, f"需要 0.01° 全球格网 36000×18000，实际 {shape[1]}×{shape[0]}" if shape else "无法读取")
                else:
                    put(key, True, "0.01° 全球格网")
        if task["soil_emis_b1"] and task["soil_emis_b1"] == task["soil_emis_b2"]:
            fields["soil_emis_b2"].update(ok=False, message="两个波段选了同一个文件")
    result["ok"] = all(f["ok"] for f in fields.values())
    return result


def describe_types() -> dict:
    return {key: {k: v for k, v in value.items()} for key, value in TYPES.items()}
