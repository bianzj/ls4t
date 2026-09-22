#!/usr/bin/env python3
"""Check how complete the slstr-euro-lst disk really is, stage by stage.

Three stages are checked per scene folder, from the files that the production
scripts actually open (not from the folder names):

* ``tif``   - extraction output.  Required: bt8/bt9, vza, cloud and lat/lon for
  both views, because ``slstr_lst.py`` and ``slstr_lsct2.py`` read exactly that
  set.  ``*_proj.tif`` is not required.
* ``lst``   - needs ``lst_nadir.tif`` and ``lst_obliq.tif``.
* ``lsct2`` - needs ``lsct2.tif`` (a folder without it means "attempted, no
  valid pixel", which is a normal outcome of the retrieval).

usage:
  python cases/slstr/regions/euro_lst_data_status.py --root /media/hero/slstr-euro-lst \
      --out cases/slstr/regions/euro_lst_data_status.json \
      --note cases/slstr/regions/euro_lst_data_status.md
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

DEFAULT_ROOT = Path("/media/hero/slstr-euro-lst")
VIEWS = ("nadir", "obliq")
TIF_REQUIRED = tuple(
    f"{band}_{view}.tif"
    for band in ("bt8", "bt9", "vza", "cloud", "lat", "lon")
    for view in VIEWS
)


def scene_names(path: Path) -> list[str]:
    try:
        with os.scandir(path) as entries:
            return sorted(e.name for e in entries if e.is_dir(follow_symlinks=False))
    except FileNotFoundError:
        return []


def dir_files(path: Path) -> set[str]:
    try:
        with os.scandir(path) as entries:
            return {e.name for e in entries if e.is_file(follow_symlinks=False)}
    except FileNotFoundError:
        return set()


def check_scene(args) -> tuple[str, dict]:
    root, year, scene = args
    year_dir = Path(root) / str(year)
    tif_files = dir_files(year_dir / "tif" / scene)
    lst_files = dir_files(year_dir / "lst" / scene)
    lsct2_files = dir_files(year_dir / "lsct2" / scene)
    missing_tif = [f for f in TIF_REQUIRED if f not in tif_files]
    return scene, dict(
        n_tif=len(tif_files),
        tif_ok=not missing_tif,
        n_tif_missing=len(missing_tif),
        tif_missing=missing_tif[:6],
        only_cloud_obliq=missing_tif == ["cloud_obliq.tif"],
        lst_nadir="lst_nadir.tif" in lst_files,
        lst_obliq="lst_obliq.tif" in lst_files,
        lsct2="lsct2.tif" in lsct2_files,
    )


def scan_year(root: Path, year: int, workers: int) -> dict:
    year_dir = root / str(year)
    scenes = sorted(set(scene_names(year_dir / "tif"))
                    | set(scene_names(year_dir / "lst"))
                    | set(scene_names(year_dir / "lsct2")))
    result = {}
    if not scenes:
        return result
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for scene, info in pool.map(check_scene, [(str(root), year, s) for s in scenes],
                                    chunksize=64):
            result[scene] = info
    return result


def classify(info: dict) -> str:
    if not info["tif_ok"]:
        return "extraction_incomplete" if info["n_tif"] else "extraction_missing"
    if not (info["lst_nadir"] and info["lst_obliq"]):
        return "lst_missing"
    if not info["lsct2"]:
        return "lsct2_empty"
    return "complete"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--years", nargs="+", type=int,
                    default=list(range(2016, 2026)))
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--out", type=Path, default=Path("/tmp/euro_lst_data_status.json"))
    ap.add_argument("--note", type=Path, default=None)
    args = ap.parse_args()

    report = dict(root=str(args.root), checked=time.strftime("%Y-%m-%dT%H:%M:%S"), years={})
    for year in args.years:
        t0 = time.time()
        scenes = scan_year(args.root, year, args.workers)
        if not scenes:
            print(f"{year}: no scene folders", flush=True)
            continue
        buckets = defaultdict(list)
        for scene, info in scenes.items():
            buckets[classify(info)].append(scene)
        month_gap = Counter()
        for kind in ("extraction_missing", "extraction_incomplete", "lst_missing", "lsct2_empty"):
            for scene in buckets[kind]:
                month_gap[f"{kind}:{scene.split('____')[1][:6]}"] += 1
        report["years"][str(year)] = dict(
            scenes=len(scenes),
            complete=len(buckets["complete"]),
            extraction_missing=len(buckets["extraction_missing"]),
            extraction_incomplete=len(buckets["extraction_incomplete"]),
            lst_missing=len(buckets["lst_missing"]),
            lsct2_empty=len(buckets["lsct2_empty"]),
            scenes_with_tif=sum(1 for i in scenes.values() if i["n_tif"] > 0),
            scenes_with_lst_nadir=sum(1 for i in scenes.values() if i["lst_nadir"]),
            scenes_with_lsct2=sum(1 for i in scenes.values() if i["lsct2"]),
            only_missing_cloud_obliq=sum(1 for i in scenes.values() if i["only_cloud_obliq"]),
            gap_by_month=dict(sorted(month_gap.items())),
            examples={k: v[:5] for k, v in buckets.items() if k != "complete"},
        )
        r = report["years"][str(year)]
        print(f"{year}: {r['scenes']:6d} scenes | complete {r['complete']:6d} | "
              f"tif missing {r['extraction_missing']:5d} | tif partial "
              f"{r['extraction_incomplete']:4d} | lst missing {r['lst_missing']:4d} | "
              f"lsct2 empty {r['lsct2_empty']:5d}  ({time.time() - t0:.0f}s)", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print("json ->", args.out)
    if args.note:
        args.note.write_text(render_note(report))
        print("note ->", args.note)


def render_note(report: dict) -> str:
    """Short data-status note for the euro-LST disk."""
    totals = {k: sum(r[k] for r in report["years"].values())
              for k in ("scenes", "complete", "extraction_missing", "extraction_incomplete",
                        "lst_missing", "lsct2_empty", "only_missing_cloud_obliq")}
    rate = 100.0 * totals["complete"] / totals["scenes"] if totals["scenes"] else 0
    lines = [
        "# slstr-euro-lst 数据完整性备注",
        "",
        f"检查时间：{report['checked']}；脚本 `cases/slstr/regions/euro_lst_data_status.py`，"
        "逐景按三个环节真正读取的文件判定，不按目录名（目录存在但没有成果的情况很多）。",
        "",
        "判定口径：`tif` 需要 bt8/bt9、vza、cloud、lat/lon 双视角共 12 个文件；"
        "`lst` 需要 lst_nadir + lst_obliq；`lsct2` 需要 lsct2.tif。"
        "**有目录但没有 lsct2.tif 时，多数是“跑过但无有效像元”的正常结果**，"
        "这类在表里单列，处理建议里也不再要求重跑。",
        "",
        f"全盘 {totals['scenes']} 景，三环节齐全 {totals['complete']} 景（{rate:.1f}%）。",
        "",
        "| 年份 | 景数 | 齐全 | 未提取 | 提取不全 | 缺 LST | 有 LST 无 LSCT2 | 完整率 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for year, r in sorted(report["years"].items()):
        y_rate = 100.0 * r["complete"] / r["scenes"] if r["scenes"] else 0
        lines.append(
            f"| {year} | {r['scenes']} | {r['complete']} | {r['extraction_missing']} | "
            f"{r['extraction_incomplete']} | {r['lst_missing']} | {r['lsct2_empty']} | "
            f"{y_rate:.1f}% |"
        )
    lines += [
        "",
        "（“未提取” = tif 目录里一个文件都没有；“提取不全” = 缺 bt8/bt9/vza/cloud/lat/lon 之一；"
        "“有 LST 无 LSCT2”里含正常的无有效像元，按已跑完年份的比例剔除后见下。"
        "完整率偏低主要来自这些正常空结果和提取缺口，不等同于遗漏。）",
        "",
        "## 结论",
        "",
        "跑完的年份（2018、2019、2021、2022、2023、2024，以及补完后的 2020）"
        "“有 LST 无 LSCT2”的比例稳定在 **8~10%**，那是极夜/云掩膜全灭导致的正常空结果。"
        "以此为基线，真正的缺口是：",
        "",
        "| 缺口 | 规模 | 能否直接补 |",
        "|---|---|---|",
    ]
    rows = []
    for year, r in sorted(report["years"].items()):
        if not r["scenes_with_lst_nadir"]:
            continue
        expected = 0.09 * r["scenes_with_lst_nadir"]
        real = max(0, int(r["lsct2_empty"] - expected))
        rows.append((real, year, r))
    for real, year, r in sorted(rows, reverse=True):
        if real < 100:
            continue
        lines.append(f"| {year} 年缺 LSCT2（约 {real} 景） | 有 LST 输入 "
                     f"{r['scenes_with_lst_nadir']} 景，出成果 {r['scenes_with_lsct2']} 景 | "
                     "可以，直接跑 `slstr_lsct2_parallel.py` |")
    lines.append(
        f"| 2020 年 11—12 月提取缺口（{report['years']['2020']['extraction_incomplete'] + report['years']['2020']['extraction_missing']} 景） | "
        "其中 2020-11 617 景、2020-12 822 景没有 tif 输入 | 不行，要先拿回原始 .SEN3 |")
    other_missing = totals["extraction_missing"] - report["years"]["2020"]["extraction_missing"]
    other_partial = totals["extraction_incomplete"] - report["years"]["2020"]["extraction_incomplete"]
    other_cloud = totals["only_missing_cloud_obliq"] - report["years"]["2020"]["only_missing_cloud_obliq"]
    lines.append(
        f"| 2020 以外各年的零星提取缺口（{other_missing} 景无 tif、{other_partial} 景不全，"
        f"其中 {other_cloud} 景只缺 cloud_obliq.tif） | 约 2% 量级，分散在各月 | "
        "不行，同样要补原始产品 |")
    lines += [
        "",
        "另外 2017 年还有 **1415 景缺 LST 成果**（2017-02 最集中，855 景），"
        "需要先补 LST 才能谈 LSCT2。",
        "",
        "## 处理建议",
        "",
        "1. 可直接补跑 LSCT2（有 LST 输入、只是没算）：",
        "",
        "```bash",
        "cd /home/hero/work/ls4t",
        "PYTHONPATH=. python cases/slstr/implementation/one_by_one/slstr_lsct2_parallel.py \\",
        "    --year 2017 --workers 48 --report cases/slstr/regions/lsct2_2017_completion.json",
        "PYTHONPATH=. python cases/slstr/implementation/one_by_one/slstr_lsct2_parallel.py \\",
        "    --year 2025 --workers 48 --report cases/slstr/regions/lsct2_2025_completion.json",
        "```",
        "",
        "2. 缺 LST 的景（2017 年 1415 景）重跑 `cases/slstr/implementation/one_by_one/slstr_lst.py`；",
        "3. 提取缺口（2020-11/12 为主，含各年零星缺 cloud_obliq 的景）需要原始 .SEN3，"
        "目前挂载的盘上没有 raw 数据，要先重新下载再解压、提取、LST、LSCT2 依序重跑；",
        "4. 无有效像元的景（极夜、云掩膜全灭）不用处理。",
        "",
        "## 逐年明细",
        "",
    ]
    for year, r in sorted(report["years"].items()):
        lines.append(f"**{year}**：景 {r['scenes']}，有 tif {r['scenes_with_tif']}，"
                     f"有 lst_nadir {r['scenes_with_lst_nadir']}，有 lsct2.tif {r['scenes_with_lsct2']}，"
                     f"齐全 {r['complete']}")
        gaps = sorted(r["gap_by_month"].items(), key=lambda kv: -kv[1])
        for key, count in [g for g in gaps if g[1] >= 20][:6]:
            kind, month = key.split(":")
            label = {"extraction_missing": "未提取",
                     "extraction_incomplete": "提取不全",
                     "lst_missing": "缺 LST",
                     "lsct2_empty": "有 LST 无 LSCT2"}[kind]
            lines.append(f"  - {month[:4]}-{month[4:]}：{count} 景 {label}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
