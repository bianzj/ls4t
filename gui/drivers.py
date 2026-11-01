"""Task implementations run by gui/worker.py (and its process-pool children).

Unzip and reformat are written here; LST and LSCT2 call the production modules
``gui.legacy.slstr_lst_scene_parallel`` and ``gui.legacy.slstr_lsct2_scene_parallel``
unchanged, one scene per call, so their numbers are exactly the production numbers.
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from gui import layout

NIGHT_MESSAGE = "夜间场景；生产算法只有白天分裂窗系数，未处理"
LSCT_WINDOW_LIMIT = 40_000_000  # base-raster pixels shipped to every LSCT2 worker


class Context:
    def __init__(self, spec: dict, emit):
        self.task = spec["task"]
        self.kind = self.task["type"]
        self.input = Path(self.task["input_dir"])
        self.output = Path(self.task["output_dir"])
        self.years = [str(y) for y in self.task["years"]]
        self.overwrite = bool(self.task.get("overwrite"))
        self.include_night = bool(self.task.get("include_night"))
        self.workers = max(1, int(spec["settings"].get("workers", 4)))
        self.emit = emit

    def start(self, scene):
        self.emit({"type": "start", "scene": scene})

    def result(self, scene, status, message=""):
        """status: done / skipped (already done or nothing to do) / failed."""
        self.emit({"type": "result", "scene": scene, "status": status, "message": message})


def _pool_results(futures, ctx: Context):
    for future in as_completed(futures):
        scene = futures[future]
        try:
            status, message = future.result()
        except Exception as error:  # noqa: BLE001
            status, message = "failed", repr(error)
        yield scene, status, message


# --------------------------------------------------------------------------- unzip

WANTED_FILES = {
    'S2_radiance_an.nc', 'S2_quality_an.nc', 'S2_radiance_ao.nc', 'S2_quality_ao.nc',
    'S3_radiance_an.nc', 'S3_quality_an.nc', 'S3_radiance_ao.nc', 'S3_quality_ao.nc',
    'geometry_tn.nc', 'geometry_to.nc', 'geodetic_in.nc', 'geodetic_io.nc', 'met_tx.nc',
    'S8_BT_in.nc', 'S8_BT_io.nc', 'S9_BT_in.nc', 'S9_BT_io.nc', 'flags_in.nc', 'flags_io.nc',
}


def _wanted():
    return WANTED_FILES


def _unzip_one(source: Path, destination: Path, overwrite: bool) -> tuple[str, str]:
    if source.is_dir():
        return "skipped", "已是解压目录"
    if (destination / "flags_io.nc").is_file() and (destination / "S8_BT_in.nc").is_file() and not overwrite:
        return "skipped", "已解压"
    partial = destination.with_name(destination.name + ".partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    wanted = _wanted()
    extracted = set()
    try:
        with zipfile.ZipFile(source) as bundle:
            for member in bundle.infolist():
                base = os.path.basename(member.filename)
                if member.is_dir() or base not in wanted:
                    continue
                # flat extraction by basename: member paths are never trusted
                with bundle.open(member) as src, (partial / base).open("wb") as dst:
                    shutil.copyfileobj(src, dst, 1 << 20)
                extracted.add(base)
    except (zipfile.BadZipFile, OSError) as error:
        shutil.rmtree(partial, ignore_errors=True)
        return "failed", f"压缩包损坏或无法读取：{error}"
    if "S8_BT_in.nc" not in extracted:
        shutil.rmtree(partial, ignore_errors=True)
        return "failed", "压缩包里没有 S8_BT_in.nc，不是完整的 SL_1_RBT 产品"
    if destination.exists():
        shutil.rmtree(destination)
    partial.rename(destination)
    missing = sorted(wanted - extracted)
    return "done", (f"缺少 {len(missing)} 个文件：{', '.join(missing[:4])}" if missing else "")


def run_unzip(ctx: Context):
    work = []
    for year in ctx.years:
        for scene, source in sorted(layout.task_inputs("unzip", ctx.input, year).items()):
            work.append((scene, source, layout.stage_dir(ctx.output, year, "raw", scene)))
    ctx.emit({"type": "total", "total": len(work)})
    with ThreadPoolExecutor(max_workers=min(4, ctx.workers)) as pool:
        futures = {}
        for scene, source, destination in work:
            ctx.start(scene)
            futures[pool.submit(_unzip_one, source, destination, ctx.overwrite)] = scene
        for scene, status, message in _pool_results(futures, ctx):
            ctx.result(scene, status, message)


# ------------------------------------------------------------------------ reformat
# Encodings follow cases/slstr-america/recover_local_raw.py (encode/extract), the
# extractor whose output the production LST/LSCT2 runs consume: signed int16
# lat/lon*100, uint16 BT*100 (0 missing), uint16 angles*100 (65535 missing),
# uint16 cloud bitmask (65535 missing), up to 1200 native scanlines.

VIEW_SPEC = (("nadir", "in", "tn", 1500, (0, 96)), ("obliq", "io", "to", 900, (36, 95)))


def _native(path: Path, variable: str) -> np.ndarray:
    from netCDF4 import Dataset

    with Dataset(path) as ds:
        values = ds.variables[variable][:]
        return np.asarray(np.ma.filled(values.astype(np.float64), np.nan))


def _encode(values, kind):
    from osgeo import gdal

    data = np.asarray(values)
    if kind == "geo":
        valid = np.isfinite(data) & (data >= -180) & (data <= 180)
        return np.where(valid, np.trunc(data * 100), -32768).astype(np.int16), gdal.GDT_Int16, -32768
    if kind == "cloud":
        valid = np.isfinite(data) & (data >= 0) & (data <= 65534)
        return np.where(valid, data, 65535).astype(np.uint16), gdal.GDT_UInt16, 65535
    valid = np.isfinite(data) & (data >= 0) & (data < 655.35)
    missing = 0 if kind == "thermal" else 65535
    return np.where(valid, np.trunc(data * 100), missing).astype(np.uint16), gdal.GDT_UInt16, missing


def _write(path: Path, values, kind):
    from osgeo import gdal

    gdal.UseExceptions()
    array, dtype, nodata = _encode(values, kind)
    tmp = path.with_suffix(".tmp.tif")
    ds = gdal.GetDriverByName("GTiff").Create(
        str(tmp), array.shape[1], array.shape[0], 1, dtype, options=["TILED=YES", "COMPRESS=DEFLATE"]
    )
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    band.WriteArray(array)
    ds.FlushCache()
    ds = None
    os.replace(tmp, path)


def _tie_grid(values, columns, shape):
    import cv2

    start, end = columns
    if values.ndim != 2 or values.shape[1] < end:
        raise ValueError("几何文件的 tie-point 列数不足")
    # Historical extractors passed INTER_NEAREST positionally into dst; the
    # interpolation that produced every existing product is INTER_LINEAR.
    return cv2.resize(values[:, start:end], (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)


def _image_grid(values, width, rows=None):
    # Supported SLSTR granules contain 1198 or 1199 scanlines as well as 1200.
    # Never pad missing rows or
    # silently accept inconsistent row counts within a view.
    if values.ndim != 2 or values.shape[0] < 1198 or values.shape[1] != width:
        raise ValueError(f"原生影像网格不受支持：{values.shape}")
    native_rows = min(1200, values.shape[0])
    if rows is not None and native_rows != rows:
        raise ValueError(f"原生影像行数不一致：{values.shape}, expected {rows}")
    return values[:native_rows, :]


def reformat_scene(native: str, out: str, overwrite: bool) -> tuple[str, str]:
    native, out = Path(native), Path(out)
    if (out / layout.SCENE_META).is_file() and not overwrite:
        return "skipped", "已重整"
    out.mkdir(parents=True, exist_ok=True)
    (out / layout.SCENE_META).unlink(missing_ok=True)
    written_views, problems, sza_center = [], [], None
    grid_shapes = {}
    for view, suffix, tie, width, columns in VIEW_SPEC:
        needed = [f"S8_BT_{suffix}.nc", f"S9_BT_{suffix}.nc", f"geodetic_{suffix}.nc", f"geometry_{tie}.nc", f"flags_{suffix}.nc"]
        missing = [n for n in needed if not (native / n).is_file()]
        if missing:
            problems.append(f"{view} 缺少 {', '.join(missing)}")
            continue
        try:
            first = _image_grid(_native(native / f"S8_BT_{suffix}.nc", f"S8_BT_{suffix}"), width)
            shape = first.shape
            for band in ("S8", "S9"):
                array = first if band == "S8" else _image_grid(
                    _native(native / f"{band}_BT_{suffix}.nc", f"{band}_BT_{suffix}"), width, shape[0])
                _write(out / f"bt{8 if band == 'S8' else 9}_{view}.tif", array, "thermal")
            for field, var in (("lat", "latitude"), ("lon", "longitude")):
                array = _image_grid(_native(native / f"geodetic_{suffix}.nc", f"{var}_{suffix}"), width, shape[0])
                _write(out / f"{field}_{view}.tif", array, "geo")
            for field, var in (("vza", "sat_zenith"), ("vaa", "sat_azimuth"), ("sza", "solar_zenith"), ("saa", "solar_azimuth")):
                grid = _tie_grid(_native(native / f"geometry_{tie}.nc", f"{var}_{tie}"), columns, shape)
                _write(out / f"{field}_{view}.tif", grid, "angle")
                if view == "nadir" and field == "sza":
                    # same rule as slstr_data_scene_origin.py: nadir SZA at pixel [500, 500]
                    value = float(grid[500, 500])
                    sza_center = value if np.isfinite(value) else None
            cloud = _image_grid(_native(native / f"flags_{suffix}.nc", f"cloud_{suffix}"), width, shape[0])
            _write(out / f"cloud_{view}.tif", cloud, "cloud")
            written_views.append(view)
            grid_shapes[view] = list(shape)
        except Exception as error:  # noqa: BLE001
            problems.append(f"{view} 读取失败：{error}")
    if not written_views:
        return "failed", "；".join(problems) or "没有可用视角"
    meta = {
        "scene": out.name,
        "native": str(native),
        "views": written_views,
        "grid_shapes": grid_shapes,
        "sza_center_deg": sza_center,
        "daytime": None if sza_center is None else bool(0 <= sza_center < 85),
        "encoding": "lat/lon int16 deg*100; bt uint16 K*100 (0 missing); angles uint16 deg*100 (65535 missing); cloud uint16 bitmask",
        "problems": problems,
    }
    (out / layout.SCENE_META).write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return "done", "；".join(problems)


def prepare_scene(source: str, raw: str, tif: str, overwrite: bool) -> tuple[str, str]:
    """Unzip (when the source is an archive) and reformat one scene for LST."""
    source, raw = Path(source), Path(raw)
    if source.is_dir():
        native = source
    else:
        status, message = _unzip_one(source, raw, False)
        if status == "failed":
            return status, message
        native = raw
    return reformat_scene(str(native), tif, overwrite)


# ----------------------------------------------------------------------------- LST


def load_tcwv_cm_any(path: Path) -> np.ndarray:
    """Production decoder extended to the TCWV layouts found on this machine.

    Known layouts (24 x 721 x 1440, north to south): /data float32 kg m-2 (2021+),
    /tcw float32 kg m-2 (2018), /tcw uint16 kg m-2 * 100 without scale_factor (2017),
    /tcwv float64 kg m-2 (2019-2020). Hours that are all zero are missing data and
    become NaN, so a scene acquired in such an hour is reported, not retrieved.
    """
    import h5py

    with h5py.File(path, "r") as handle:
        key = next((n for n in ("data", "tcw", "tcwv") if n in handle), None)
        if key is None:
            raise ValueError(f"{path.name}: 没有 data/tcw/tcwv 数据集")
        field = handle[key]
        if field.shape != (24, 721, 1440):
            raise ValueError(f"{path.name}: TCWV 网格不受支持 {field.shape}")
        cube = np.asarray(field[...], dtype=np.float32)
        if "scale_factor" in field.attrs or "add_offset" in field.attrs:
            cube = cube * float(field.attrs.get("scale_factor", 1.0)) + float(field.attrs.get("add_offset", 0.0))
        elif np.issubdtype(field.dtype, np.integer):
            cube = cube / 100.0
    cube = cube / 10.0
    finite = cube[np.isfinite(cube)]
    if finite.size == 0 or finite.min() < 0 or finite.max() > 20:
        raise ValueError(f"{path.name}: TCWV 超出 0–20 cm，编码或单位不明")
    empty_hours = ~np.any(cube.reshape(24, -1) > 0, axis=1)
    cube[empty_hours] = np.nan
    return cube


def _lst_init(root, base, emis_pair, type_ref, tcwv_root, lai_root, overwrite):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from gui.legacy import slstr_lst_scene_parallel as lst

    lst.load_tcwv_cm = load_tcwv_cm_any
    # find_base_file(base, name) returns an absolute ``name`` unchanged, so the two
    # chosen soil-emissivity bands are passed as full paths
    lst._init_worker_from_files(root, base, type_ref, tuple(emis_pair), root, tcwv_root, overwrite, lai_root)


def _translate(error: str) -> str:
    if error.startswith("missing LAI") or error.startswith("no LAI file"):
        return "找不到这一天对应的 LAI 文件"
    if error.startswith("missing TCWV"):
        return "找不到这一天的 TCWV 文件"
    return error


def _lst_scene(task):
    from gui.legacy import slstr_lst_scene_parallel as lst

    day, scene = task
    stats = lst.process_day((day, [scene]))
    if stats["error"]:
        return "failed", _translate(stats["error"])
    hour = int(scene.split("____")[1][9:11])
    cube = lst._STATE.get("tcw_day")
    if cube is not None and not np.isfinite(cube[hour]).any():
        year = scene.split("____")[1][:4]
        for view in layout.VIEWS:
            (lst._STATE["out_root"] / year / "lst" / scene / f"lst_{view}.tif").unlink(missing_ok=True)
        return "failed", f"TCWV 文件中 {hour:02d} 时整层为 0（数据缺失），未反演"
    real_errors = [e for e in stats["scene_errors"] if "lack usable input" not in e.get("error", "")]
    if real_errors:
        return "failed", "；".join(f"{e.get('view', '')} {e['error']}" for e in real_errors)
    if stats["empty"]:
        return "done", "没有有效像元（云、水体、冰雪或超出 220–365 K）"
    return "done", ""


def run_lst(ctx: Context):
    t = ctx.task
    work = []
    for year in ctx.years:
        for scene, source in sorted(layout.task_inputs("lst", ctx.input, year).items()):
            work.append((year, scene, source))
    ctx.emit({"type": "total", "total": len(work)})

    # 1. unzip if needed and reformat to swath GeoTIFF
    ready = []
    with ProcessPoolExecutor(max_workers=max(1, min(ctx.workers, len(work)))) as pool:
        futures = {}
        for year, scene, source in work:
            ctx.start(scene)
            raw = layout.stage_dir(ctx.output, year, "raw", scene)
            tif = layout.stage_dir(ctx.output, year, "tif", scene)
            futures[pool.submit(prepare_scene, str(source), str(raw), str(tif), ctx.overwrite)] = (year, scene)
        for (year, scene), status, message in _pool_results(futures, ctx):
            if status == "failed":
                ctx.result(scene, "failed", f"重整失败：{message}")
            else:
                ready.append((year, scene))

    # 2. split-window LST with the production module
    tasks = []
    for year, scene in ready:
        tif = layout.stage_dir(ctx.output, year, "tif", scene)
        meta = layout.read_scene_meta(tif) or {}
        if not ctx.include_night and meta.get("daytime") is False:
            ctx.result(scene, "skipped", NIGHT_MESSAGE)
            continue
        possible = layout.views_with(tif, "{band}_{view}.tif", ("bt8", "bt9", "vza", "lat", "lon"))
        produced = layout.views_with(layout.stage_dir(ctx.output, year, "lst", scene), "lst_{view}.tif")
        if not ctx.overwrite and set(possible) <= set(produced):
            ctx.result(scene, "skipped", "已有 LST 结果")
            continue
        tasks.append((scene.split("____")[1][:8], scene))
    if not tasks:
        return
    workers = min(ctx.workers, len(tasks))
    print(f"LST：{len(tasks)} 景，{workers} 个进程；每个进程先加载全球土壤发射率和类型图（约 5 GB），需要一两分钟", flush=True)
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_lst_init,
        initargs=(str(ctx.output), t["aux_dir"], (t["soil_emis_b1"], t["soil_emis_b2"]), t["type_map"], t["tcwv_root"], t["lai_root"], True),
    ) as pool:
        futures = {pool.submit(_lst_scene, task): task[1] for task in sorted(tasks)}
        for scene, status, message in _pool_results(futures, ctx):
            ctx.result(scene, status, message)


# ---------------------------------------------------------------------------- LSCT


def lai_file_in(lai_root: Path, year: int, day) -> Path | None:
    """LAI lookup of slstr_lst_scene_parallel.lai_file with an explicit root."""
    from datetime import date

    doy4 = (((day - date(year, 1, 1)).days + 1) // 4) * 4 + 1
    folder = "lai_2002-2020_0p01deg" if year <= 2020 else "lai_2021-2025_0p01deg"
    for root in (lai_root / str(year), lai_root / folder / str(year)):
        for prefix in ("LAI", "lai"):
            path = root / f"{prefix}_{year}{doy4:03d}.h5"
            if path.is_file():
                return path
    return None


def lsct_state(task: dict, window) -> dict:
    """slstr_lsct2_scene_parallel.load_state with the task's chosen files.

    Same window reads, dtypes and scaling; the night coefficients it also loads are
    never used by the retrieval and are omitted.
    """
    from base.files import read_txt_array
    from osgeo import gdal

    row0, row1, col0, col1 = window

    def read_window(path, dtype):
        dataset = gdal.Open(str(path))
        data = dataset.ReadAsArray(col0, row0, col1 - col0, row1 - row0)
        if data is None:
            raise OSError(f"无法读取底图窗口：{path}")
        return np.asarray(data, dtype=dtype)

    emis1 = read_window(task["soil_emis_b1"], np.float32)
    emis1 /= 1000.0
    emis2 = read_window(task["soil_emis_b2"], np.float32)
    emis2 /= 1000.0
    reference = gdal.Open(str(task["type_map"]))
    aux = Path(task["aux_dir"])
    table = next(p for p in (aux / "IGBP_Emi.txt", aux / "emis" / "IGBP_Emi.txt", aux / "base" / "IGBP_Emi.txt") if p.is_file())
    return dict(
        emis1_s0=emis1,
        emis2_s0=emis2,
        classif0=read_window(task["type_map"], np.uint8),
        grid_shape=(reference.RasterYSize, reference.RasterXSize),
        window=window,
        emis_v=read_txt_array(str(table), 0, 2),
    )


def _lsct_init(state, root, out_root, type_ref, lai_root):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from gui.legacy import slstr_lsct2_scene_parallel as lsct

    lsct.lai_file = lambda year, day: lai_file_in(Path(lai_root), year, day)
    lsct._init_worker(state, root, out_root, "lsct", type_ref)


LSCT_REASONS = {
    "water": "足迹内全是水体",
    "non_land": "足迹内没有陆地类型",
    "low_lai": "LAI 太低，无法分解组分",
    "invalid_thermal": "LST 或亮温无效",
    "cloud": "全部被云覆盖",
    "regression": "窗口回归没有有效解",
}


def _lsct_scene(task):
    from gui.legacy import slstr_lsct2_scene_parallel as lsct

    day, scene = task
    stats = lsct.process_day((day, [scene]))
    if stats["error"]:
        return "failed", _translate(stats["error"].split(": ", 1)[-1] if ": " in stats["error"] else stats["error"])
    if stats["written"]:
        return "done", "云掩膜回退" if stats["cloud_fallback"] else ""
    if stats["empty"]:
        reason = next(iter(stats["empty_reasons"]), "")
        return "done", "没有有效像元：" + LSCT_REASONS.get(reason, reason)
    return "failed", "缺少 LST 或重整输入"


def _windows(lsct, root: Path, items, type_ref):
    """Greedy groups of scenes whose combined base-raster window stays small."""
    boxes = []
    for year, day, scene in items:
        try:
            box = lsct.scene_window(root, int(year), {day: [scene]}, [day], type_ref)
        except Exception:  # noqa: BLE001
            box = None
        boxes.append((box, (day, scene)))
    groups = []
    for box, item in sorted((b for b in boxes if b[0]), key=lambda b: (b[0][2], b[0][0])):
        if groups:
            r0, r1, c0, c1 = groups[-1][0]
            merged = (min(r0, box[0]), max(r1, box[1]), min(c0, box[2]), max(c1, box[3]))
            if (merged[1] - merged[0]) * (merged[3] - merged[2]) <= LSCT_WINDOW_LIMIT:
                groups[-1] = (merged, groups[-1][1] + [item])
                continue
        groups.append((box, [item]))
    invalid = [item for box, item in boxes if not box]
    return groups, invalid


def run_lsct(ctx: Context):
    from gui.legacy import slstr_lsct2_scene_parallel as lsct

    t = ctx.task
    work = []
    for year in ctx.years:
        for scene in sorted(layout.task_inputs("lsct", ctx.input, year)):
            work.append((year, scene))
    ctx.emit({"type": "total", "total": len(work)})
    items = []
    for year, scene in work:
        tif = layout.stage_dir(ctx.input, year, "tif", scene)
        if len(layout.views_with(layout.stage_dir(ctx.input, year, "lst", scene), "lst_{view}.tif")) < 2:
            ctx.result(scene, "failed", "需要天底和后向两个视角的 LST")
            continue
        if "obliq" not in layout.views_with(tif, "{band}_{view}.tif", ("bt8", "bt9", "vza", "lat", "lon")):
            ctx.result(scene, "failed", "输入目录里缺少这一景的斜视重整结果（年份/tif）")
            continue
        if not ctx.include_night and (layout.read_scene_meta(tif) or {}).get("daytime") is False:
            ctx.result(scene, "skipped", NIGHT_MESSAGE)
            continue
        out = layout.stage_dir(ctx.output, year, "lsct", scene)
        if ((out / "lsct2.tif").is_file() or (out / layout.LSCT_EMPTY_MARKER).is_file()) and not ctx.overwrite:
            ctx.result(scene, "skipped", "已有 LSCT 结果")
            continue
        (out / "lsct2.tif").unlink(missing_ok=True)
        (out / layout.LSCT_EMPTY_MARKER).unlink(missing_ok=True)
        items.append((year, scene.split("____")[1][:8], scene))
    if not items:
        return
    groups, invalid = _windows(lsct, ctx.input, items, Path(t["type_map"]))
    for _, scene in invalid:
        ctx.result(scene, "failed", "斜视经纬度全部无效")
    for index, (window, group) in enumerate(groups, 1):
        rows, cols = window[1] - window[0], window[3] - window[2]
        print(f"LSCT 批次 {index}/{len(groups)}：{len(group)} 景，底图窗口 {rows}×{cols}", flush=True)
        state = lsct_state(t, window)
        with ProcessPoolExecutor(
            max_workers=min(ctx.workers, len(group)),
            initializer=_lsct_init,
            initargs=(state, str(ctx.input), str(ctx.output), t["type_map"], t["lai_root"]),
        ) as pool:
            futures = {}
            for task in sorted(group):
                ctx.start(task[1])
                futures[pool.submit(_lsct_scene, task)] = task[1]
            for scene, status, message in _pool_results(futures, ctx):
                ctx.result(scene, status, message)
        del state


RUNNERS = {"unzip": run_unzip, "lst": run_lst, "lsct": run_lsct}
