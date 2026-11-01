"""Folder layout and scene discovery shared by the GUI server and the task worker.

Output folders follow the layout the production scripts in cases/slstr use, so results
made here and on the command line are interchangeable::

    <output>/<year>/raw/<scene>.SEN3/*.nc      unzip task: native files (19-file subset)
    <output>/<year>/tif/<scene>.SEN3/*.tif     LST task: swath GeoTIFFs read by LST and LSCT2
    <output>/<year>/lst/<scene>.SEN3/lst_{nadir,obliq}.tif
    <output>/<year>/lsct/<scene>.SEN3/lsct2.tif
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

VIEWS = ("nadir", "obliq")
SCENE_PATTERN = re.compile(r"^S3[AB]_SL_1_RBT_")
SCENE_META = "scene.json"
LSCT_EMPTY_MARKER = "_no_valid_pixel.json"


def scene_name(path: Path) -> str:
    name = path.name
    if name.lower().endswith(".zip"):
        name = name[:-4]
    if not name.endswith(".SEN3"):
        name += ".SEN3"
    return name


def parse_name(name: str) -> dict:
    stamp = re.findall(r"\d{8}T\d{6}", name)
    start = stamp[0] if stamp else ""
    return {"sat": name[:3], "start": start, "day": start[:8]}


def _source_dirs(root: Path, year: str) -> list[Path]:
    base = root / year
    return [d for d in (root, base, base / "raw", base / "zip") if d.is_dir()]


def find_sources(root: str | Path, year: str) -> dict[str, Path]:
    """SL_1_RBT products of one year: ``.SEN3.zip`` archives or unzipped ``.SEN3`` folders.

    Products may sit in ``<root>/<year>/``, ``<root>/<year>/raw|zip/`` or flat in ``<root>``;
    flat products are assigned to the year of their start time.
    """
    found: dict[str, Path] = {}
    root = Path(root)
    for folder in _source_dirs(root, str(year)):
        with os.scandir(folder) as entries:
            for entry in entries:
                if not SCENE_PATTERN.match(entry.name):
                    continue
                if folder == root and parse_name(entry.name)["start"][:4] != str(year):
                    continue
                is_zip = entry.is_file() and entry.name.lower().endswith(".zip")
                is_dir = entry.is_dir() and entry.name.endswith(".SEN3")
                if is_zip or is_dir:
                    name = scene_name(Path(entry.path))
                    # an unzipped folder wins over its archive
                    if name not in found or is_dir:
                        found[name] = Path(entry.path)
    return found


def years(root: str | Path) -> list[str]:
    """Year folders of ``root`` plus the years of products lying flat in it."""
    root = Path(root)
    result = set()
    if root.is_dir():
        with os.scandir(root) as entries:
            for entry in entries:
                if entry.is_dir() and re.fullmatch(r"(19|20)\d\d", entry.name):
                    result.add(entry.name)
                elif SCENE_PATTERN.match(entry.name):
                    start = parse_name(entry.name)["start"]
                    if start:
                        result.add(start[:4])
    return sorted(result, reverse=True)


def task_inputs(kind: str, input_dir: str | Path, year: str) -> dict[str, Path]:
    """Scenes of one year that a task of ``kind`` would process: {scene name: source}."""
    root = Path(input_dir)
    if not root.is_dir():
        return {}
    if kind == "unzip":
        return {n: p for n, p in find_sources(root, year).items() if p.is_file()}
    if kind == "lst":
        return find_sources(root, year)
    lst = root / str(year) / "lst"
    if not lst.is_dir():
        return {}
    return {p.name: p for p in sorted(lst.iterdir()) if p.is_dir() and SCENE_PATTERN.match(p.name)}


def stage_dir(root: str | Path, year: str, layer: str, name: str = "") -> Path:
    path = Path(root) / str(year) / layer
    return path / name if name else path


def read_scene_meta(tif_scene: Path) -> dict | None:
    path = tif_scene / SCENE_META
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def views_with(folder: Path, pattern: str, bands=None) -> list[str]:
    """Views for which ``pattern.format(view=..., band=...)`` exists for every band."""
    result = []
    for view in VIEWS:
        names = [pattern.format(view=view, band=b) for b in (bands or [""])]
        if all((folder / n).is_file() for n in names):
            result.append(view)
    return result
