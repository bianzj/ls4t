"""Run the official regional entry for one real scene without touching products.

Uses the existing source verbatim except for paths and date/hour loop bounds.
--decode signed is an explicitly labelled diagnostic correction of signed
Celsius x100 bits stored in the projected uint16 TIFFs; it is not a production
release. All changes, dependencies, inputs and comparisons are recorded.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import difflib
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


class Tee:
    def __init__(self, stream, log):
        self.stream, self.log = stream, log

    def write(self, text):
        self.stream.write(text)
        self.log.write(text)
        self.log.flush()

    def flush(self):
        self.stream.flush()
        self.log.flush()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Source has changed: expected one occurrence of {old!r}")
    return source.replace(old, new, 1)


def comparison(new_path, archive_path):
    import h5py
    import numpy as np

    with h5py.File(new_path) as nf, h5py.File(archive_path) as af:
        nd, ad = nf["data"], af["data"]
        if nd.shape != ad.shape:
            raise ValueError(f"Shape differs: {nd.shape} vs {ad.shape}")
        if not np.array_equal(nd.attrs["GeoTransform"], ad.attrs["GeoTransform"]):
            raise ValueError("GeoTransform differs from archived scene")
        if nd.attrs["Projection"] != ad.attrs["Projection"]:
            raise ValueError("Projection differs from archived scene")
        if nd.dtype != np.dtype("uint16") or nd.attrs["Scale_Factor"] != 100:
            raise ValueError("Unexpected output encoding")
        new, old = nd[...], ad[...]
    nv, ov = np.all(new != 0, axis=0), np.all(old != 0, axis=0)
    if not nv.any():
        raise ValueError("Retrieval produced no valid four-band pixels")
    joint = nv & ov
    result = {
        "shape": list(new.shape), "dtype": str(new.dtype),
        "new_valid_pixels": int(nv.sum()), "archive_valid_pixels": int(ov.sum()),
        "common_valid_pixels": int(joint.sum()),
        "new_only_pixels": int((nv & ~ov).sum()),
        "archive_only_pixels": int((ov & ~nv).sum()),
        "exact_array_equal": bool(np.array_equal(new, old)),
        "same_mask": bool(np.array_equal(nv, ov)),
        "sunlit_below_shaded_pixels": int(((new[2] < new[3]) & nv).sum()),
        "soil_outside_sunlit_shaded_interval_pixels": int(
            (((new[0].astype(int) < new[3].astype(int) - 1) |
              (new[0].astype(int) > new[2].astype(int) + 1)) & nv).sum()),
        "bands": {},
    }
    for k, name in enumerate(("ts", "tv", "tss", "tsh")):
        x = new[k, nv].astype(float) / 100
        delta = (new[k, joint].astype(float) - old[k, joint].astype(float)) / 100
        if np.any((x < 250) | (x > 350)):
            raise ValueError(f"Out-of-range result in band {name}")
        result["bands"][name] = {
            "min_K": float(x.min()), "max_K": float(x.max()),
            "mean_K": float(x.mean()),
            "bias_vs_archive_K": float(delta.mean()) if delta.size else None,
            "mae_vs_archive_K": float(np.abs(delta).mean()) if delta.size else None,
            "rmse_vs_archive_K": float(np.sqrt(np.mean(delta ** 2))) if delta.size else None,
            "max_abs_diff_K": float(np.abs(delta).max()) if delta.size else None,
            "exact_common_pixels": int((delta == 0).sum()),
        }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", type=Path, default=Path("E:/"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--timestamp", default="latest", help="latest or YYYYMMDDHH00 (UTC)")
    p.add_argument("--decode", choices=("baseline", "signed"), default="baseline")
    args = p.parse_args()
    repo = Path(__file__).resolve().parents[3]
    source_path = Path(__file__).with_name("msg_lsct3.2-iter.py")
    sys.path.insert(0, str(repo))
    os.environ.setdefault("MPLBACKEND", "Agg")
    import h5py
    import numpy as np
    from osgeo import gdal

    gdal.UseExceptions()
    archive_root = args.data_root / "PRODUCTS/LSCT/MLST_COMPONENT"
    if args.timestamp == "latest":
        # Observation timestamps, not file modification/copy times.
        years = sorted((x for x in archive_root.iterdir() if x.is_dir() and
                        x.name.isdecimal() and len(x.name) == 4), reverse=True)
        files = []
        for year in years:
            files = sorted(year.rglob("MSG_LSCT_????????????.h5"), reverse=True)
            if files:
                break
        if not files:
            raise FileNotFoundError("No archived regional daily scenes")
        timestamp = files[0].stem.removeprefix("MSG_LSCT_")
    else:
        timestamp = args.timestamp
    date = dt.datetime.strptime(timestamp, "%Y%m%d%H%M")
    if date.minute != 0:
        raise ValueError("The official script processes whole-hour scenes")
    suffix = f"{date.year:04d}/{date.month:02d}/{date.day:02d}"
    archive = archive_root / suffix / f"MSG_LSCT_{timestamp}.h5"
    relative = {
        "LST_EURO": f"PRODUCTS/MSG/MLST/GEOTIFF/{suffix}/HDF5_LSASAF_MSG_LST_MSG-Disk_{timestamp}.tif",
        "LST_IODC": f"PRODUCTS/MSG-IODC/MLST/GEOTIFF/{suffix}/HDF5_LSASAF_MSG-IODC_LST_IODC-Disk_{timestamp}.tif",
        "LAI": f"PRODUCTS/MSG/MDLAI/GEOTIFF/{suffix}/HDF5_LSASAF_MSG_LAI_MSG-Disk_{date:%Y%m%d}0000.tif",
        "VZA_EURO": "Static/combined_euro_vza.tif",
        "VAA_EURO": "Static/combined_euro_vaa.tif",
        "VZA_IODC": "Static/combined_iodc_vza.tif",
        "VAA_IODC": "Static/combined_iodc_vaa.tif",
        "LANDCOVER": "map/MCD12C1_2011_0.01.tif",
        "SOIL_EMISSIVITY": "lse/AG1km.v003.SoilEmi.ABI.Global.001D_LSE12.tif",
        "VEGETATION_EMISSIVITY": "lse/IGBP_Emi.txt",
    }
    inputs = {k: args.data_root / v for k, v in relative.items()}
    missing = [str(x) for x in [*inputs.values(), archive] if not x.is_file()]
    if missing:
        raise FileNotFoundError("Missing local inputs: " + ", ".join(missing))
    variant = args.output.resolve() / args.decode
    variant.mkdir(parents=True, exist_ok=True)
    output = variant / suffix / f"MSG_LSCT_{timestamp}.h5"
    if output.exists():
        raise FileExistsError(f"Refusing to reuse/overwrite an existing test scene: {output}")
    source = source_path.read_text(encoding="utf-8")
    effective = replace_once(source, 'indir = "/media/hero/MSG/"',
                             f"indir = {str(args.data_root.resolve()).replace(chr(92), '/')!r}")
    effective = replace_once(effective, "outdir_root = indir + '/PRODUCTS/LSCT/MLST_COMPONENT/'",
                             f"outdir_root = {str(variant).replace(chr(92), '/')!r}")
    for name, bounds, value in (("kyear", "2017, 2018", date.year),
                                ("kmonth", "8, 13", date.month),
                                ("kday", "1, 32", date.day),
                                ("khour", "9, 17", date.hour)):
        effective = replace_once(effective, f"for {name} in range({bounds}):",
                                 f"for {name} in range({value}, {value + 1}):")
    if args.decode == "signed":
        for name in ("e", "i"):
            old = f"lst_{name} = lst_{name} / 100.0 + 273.15"
            new = f"lst_{name} = lst_{name}.view(np.int16).astype(np.float64) / 100.0 + 273.15"
            effective = replace_once(effective, old, new)
    (variant / "runtime_changes.diff").write_text("".join(difflib.unified_diff(
        source.splitlines(True), effective.splitlines(True),
        fromfile=str(source_path), tofile=f"runtime/{args.decode}")), encoding="utf-8")
    with (variant / "run.log").open("w", encoding="utf-8") as log:
        with contextlib.redirect_stdout(Tee(sys.stdout, log)), contextlib.redirect_stderr(Tee(sys.stderr, log)):
            manifest = {
                "status": "preflight", "timestamp_UTC": date.isoformat() + "Z",
                "mode": args.decode, "scope": "one full regional grid, actual official source",
                "source": str(source_path), "source_sha256": sha256(source_path),
                "runner": str(Path(__file__).resolve()), "runner_sha256": sha256(__file__),
                "effective_source_sha256": hashlib.sha256(effective.encode()).hexdigest(),
                "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
                "parameters": {"lambda": 100.0, "dif_radiance": 3, "hspot": 0.2,
                               "altitude_m": 0, "wavelength_um": 10.5},
                "runtime": {"python": sys.version, "executable": sys.executable,
                            "GDAL": gdal.VersionInfo(),
                            "packages": {name: importlib.metadata.version(name) for name in
                                         ("numpy", "scipy", "pandas", "h5py", "pvlib", "pyresample")}},
                "inputs": {}, "archive": {"path": str(archive), "sha256": sha256(archive)},
                "output": str(output),
                "limitations": [
                    "Single-scene execution does not establish provenance of all historical batches.",
                    "Projected TIFF NoData=0 is ambiguous with genuine 0 Celsius observations.",
                    "Comparison with archived retrieval is reproducibility checking, not independent validation.",
                    "Static IODC angle provenance and the 2022 orbital change need a separate audit.",
                ],
            }
            start = time.monotonic()
            print(f"Preflight: {timestamp} UTC, {args.decode}, output {output}", flush=True)
            for name, path in inputs.items():
                print(f"Fingerprint: {name}", flush=True)
                item = {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
                if path.suffix == ".tif":
                    ds = gdal.Open(str(path))
                    item.update(shape=[ds.RasterYSize, ds.RasterXSize],
                                dtype=gdal.GetDataTypeName(ds.GetRasterBand(1).DataType),
                                geotransform=list(ds.GetGeoTransform()),
                                nodata=ds.GetRasterBand(1).GetNoDataValue())
                    if name.startswith("LST_"):
                        raw = ds.ReadAsArray()
                        good = raw != 0
                        item["nonzero_pixels"] = int(good.sum())
                        item["signed_negative_pixels"] = int(((raw.view(np.int16) < 0) & good).sum())
                        del raw
                    ds = None
                manifest["inputs"][name] = item
            report = variant / "report.json"
            report.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            namespace = {"__name__": "__main__", "__file__": str(source_path)}
            try:
                manifest["status"] = "running"
                report.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
                retrieval_start = time.monotonic()
                exec(compile(effective, str(source_path), "exec"), namespace)
                manifest["retrieval_elapsed_seconds"] = time.monotonic() - retrieval_start
                if not output.is_file():
                    raise RuntimeError("Official entry returned without creating the selected scene; see run.log")
                manifest["comparison"] = comparison(output, archive)
                manifest["output_sha256"] = sha256(output)
                manifest["source_unchanged"] = sha256(source_path) == manifest["source_sha256"]
                manifest["status"] = "completed"
                print(json.dumps(manifest["comparison"], indent=2), flush=True)
            except Exception:
                manifest["status"] = "failed"
                manifest["error"] = traceback.format_exc()
                raise
            finally:
                manifest["total_elapsed_seconds"] = time.monotonic() - start
                report.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Report saved: {report}", flush=True)


if __name__ == "__main__":
    main()
