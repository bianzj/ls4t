"""Scenes a case has declared useless, so runs stop reading them again.

``cases/slstr/slstr_scene_coverage.py`` samples the geolocation pair of every
scene of one year and records the ones that have no pixel both inside the case
window and on a land-cover class the retrieval accepts.  Those scenes cannot
produce an LST or LSCT2 value for the window, so every later run would waste a
full scene of I/O on them.

The list lives next to the data: ``<scene_root>/_skip/<year>.json``.  It is
per-view, because the LST retrieval needs nadir and oblique while the LSCT2
retrieval only uses oblique.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_scene_skip(root: Path, year: int) -> dict[str, set[str]]:
    """``{scene: {views that cannot contribute}}`` from the coverage audit.

    A missing or unreadable list is not an error: the callers then behave
    exactly as before.
    """
    path = Path(root) / "_skip" / f"{year}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    scenes = data.get("scenes") or {}
    skip: dict[str, set[str]] = {}
    for scene, info in scenes.items():
        views = set(info.get("useless_views") or ())
        if not views:
            continue
        skip[scene] = views
    return skip


def is_useless(skip: dict[str, set[str]], scene: str, views: tuple[str, ...]) -> bool:
    """True when every view this stage needs is on the useless list."""
    useless = skip.get(scene)
    return bool(useless) and set(views) <= useless
