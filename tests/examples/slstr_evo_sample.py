"""Run the current SLSTR three-component scene solver on a real EVO window.

The fixture has native 10x10 windows for each view. The adapter maps the nadir
window onto the oblique window using the saved geographic nearest-neighbor
indices, then calls the production scene function without changing its solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import h5py
import numpy as np
from osgeo import gdal

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cases.slstr import slstr_lsct3_bayes_scene as retrieval  # noqa: E402

SAMPLE = REPO / "tests/data/slstr_evo_20170517_10x10"
DEFAULT_OUTPUT = REPO / "tests/outputs/slstr_evo_20170517_10x10"
YEAR = 2017


def load_sample(sample: Path = SAMPLE):
    manifest = json.loads((sample / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((sample / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Fixture checksum mismatch: {name}")
    with h5py.File(sample / "window.h5", "r") as handle:
        arrays = {}
        for view in ("nadir", "obliq"):
            for name in ("vza", "vaa", "cloud"):
                arrays[f"{name}_{view}"] = handle[f"observations/{view}/{name}"][:]
            arrays[f"lst_{view}"] = handle[f"temperature/{view}/LST_K"][:]
        for name in ("lat", "lon", "sza", "saa"):
            arrays[name] = handle[f"observations/obliq/{name}"][:]
        for name in ("LAI", "emissivity_soil_S8", "land_cover_class"):
            arrays[name] = handle[f"auxiliary/obliq/{name}"][:]
        for name in ("nearest_row", "nearest_col", "distance_km"):
            arrays[name] = handle[f"geolocation_mapping/obliq_to_nadir/{name}"][:]
    shape = tuple(manifest["shape_each_native_view"])
    if any(array.shape != shape for array in arrays.values()):
        raise ValueError("Fixture array shape mismatch")
    return manifest, arrays


def write_tif(path: Path, values: np.ndarray, *, scale: float = 1.0,
              dtype: int = gdal.GDT_Int16, missing: int = -32768) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = np.where(np.isfinite(values), np.rint(values * scale), missing)
    if dtype == gdal.GDT_UInt16:
        encoded = encoded.astype(np.uint16)
    else:
        encoded = encoded.astype(np.int16)
    height, width = encoded.shape
    dataset = gdal.GetDriverByName("GTiff").Create(str(path), width, height, 1, dtype)
    if dataset is None:
        raise OSError(f"Cannot create {path}")
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(missing)
    band.WriteArray(encoded)
    dataset.FlushCache()
    dataset = None


def run_sample(output: Path = DEFAULT_OUTPUT, sample: Path = SAMPLE,
               *, force_night: bool = False) -> dict:
    manifest, arrays = load_sample(sample)
    scene_name = manifest["scene"]
    height, width = manifest["shape_each_native_view"]
    row = arrays["nearest_row"].astype(int)
    col = arrays["nearest_col"].astype(int)
    if np.any(row < 0) or np.any(row >= height) or np.any(col < 0) or np.any(col >= width):
        raise ValueError("Nadir mapping exceeds the extracted window")
    if np.nanmax(arrays["distance_km"]) > 2:
        raise ValueError("Nadir mapping is farther than 2 km")

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="slstr_evo_", dir=output) as temporary:
        root = Path(temporary)
        src = root / str(YEAR)
        tif = src / "tif" / scene_name
        lst = src / "lst" / scene_name
        for view in ("nadir", "obliq"):
            for name in ("vza", "vaa", "cloud"):
                values = arrays[f"{name}_{view}"]
                if view == "nadir":
                    values = values[row, col]
                write_tif(tif / f"{name}_{view}.tif", values,
                          scale=1 if name == "cloud" else 100)
            values = arrays[f"lst_{view}"]
            if view == "nadir":
                values = values[row, col]
            write_tif(lst / f"lst_{view}.tif", values, scale=100,
                      dtype=gdal.GDT_UInt16, missing=0)
        for name in ("lat", "lon"):
            write_tif(tif / f"{name}_obliq.tif", arrays[name], scale=100)
        for name in ("sza", "saa"):
            values = np.full((height, width), 100.) if name == "sza" and force_night else arrays[name]
            write_tif(tif / f"{name}_obliq.tif", values, scale=100)

        state = {
            "root": root,
            "bounds": (-8.2, 38.4, -7.8, 38.7),
            "type": arrays["land_cover_class"].astype(np.int16),
            "soil_emis": np.rint(arrays["emissivity_soil_S8"] * 1000).astype(np.uint16),
            "veg_emis": np.loadtxt(sample / "IGBP_Emi.txt", dtype=np.float32)[:, 0],
        }
        lai_raw = arrays["LAI"].astype(np.float32) * 1000
        indices = np.indices((height, width))
        # The production scene expects full-scene nadir columns 548:1448 and
        # global 0.01-degree auxiliary grids. This sample supplies the saved
        # local geographic mapping and 10x10 auxiliary values instead.
        with patch.object(retrieval, "_STATE", state), \
             patch.object(retrieval, "adjust_xmin_no_g", 0), \
             patch.object(retrieval, "adjust_xmax_no_g", width), \
             patch.object(retrieval, "lai_for_scene", return_value=lai_raw), \
             patch.object(retrieval.lst_module, "grid_index", return_value=tuple(indices)):
            name, status, valid_pixels = retrieval.scene(YEAR, scene_name)
        if name != scene_name:
            raise RuntimeError("Production solver returned another scene")

        result = src / "lsct3_components" / scene_name
        temperatures = {}
        if status == "written":
            for product in retrieval.PRODUCTS:
                target = output / product
                shutil.copy2(result / product, target)
                dataset = gdal.Open(str(target))
                temperatures[product] = dataset.ReadAsArray()
                dataset = None
            valid = temperatures["vegetation.tif"] > 0
            if int(valid.sum()) != valid_pixels:
                raise ValueError("Written pixel count differs from solver status")
            for values in temperatures.values():
                if not np.all((values[valid] >= 200) & (values[valid] <= 400)):
                    raise ValueError("A component temperature is outside the solver bounds")
            if np.any(temperatures["sunlit_soil.tif"][valid] + 1e-4 <
                      temperatures["shaded_soil.tif"][valid]):
                raise ValueError("Sunlit soil is colder than shaded soil")
        elif status == "no_valid":
            for product in retrieval.PRODUCTS:
                (output / product).unlink(missing_ok=True)
        else:
            raise RuntimeError(f"Unexpected solver status: {status}")
        center = tuple(manifest["station_anchor_row_col"])
        summary = {
            "site": manifest["site"],
            "scene": scene_name,
            "method": retrieval.METHOD,
            "input": "real SLSTR 10x10 window with saved dual-view LST",
            "nadir_mapping_max_distance_km": float(np.max(arrays["distance_km"])),
            "forced_night_gate_check": force_night,
            "status": status,
            "valid_pixels": valid_pixels,
            "station_anchor_component_K": {
                name.removesuffix(".tif"): float(values[center]) if values[center] > 0 else None
                for name, values in temperatures.items()
            },
        }
        (output / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--sample", type=Path, default=SAMPLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force-night", action="store_true",
                        help="Controlled gate check: replace the saved SZA with 100 degrees")
    args = parser.parse_args()
    print(json.dumps(run_sample(args.output, args.sample, force_night=args.force_night),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
