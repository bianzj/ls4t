"""Assemble the reviewed method chapters and verify local source links.

This does not execute scientific code. Inventory hashes are checked against
the live source tree so the source snapshot cannot silently become stale.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TARGET = HERE.parent / "METHOD_INVENTORY.md"
CHAPTERS = [
    ("第一部分：卫星产品层", "satellite.md"),
    ("第二部分：组分反演、物理模型与核优化", "components.md"),
    ("第三部分：归一化、降尺度、融合与合成", "normalization_and_compositing.md"),
    ("第四部分：案例专有方法、应用及能力缺口", "cases_and_gaps.md"),
    ("第五部分：新增可配置核组合与ATC", "../KERNELS_ATC.md"),
    ("第六部分：新增TsHARP降尺度", "../TSHARP.md"),
]


def chapter_text(text: str) -> str:
    """Drop the chapter title and demote headings outside fenced code."""
    lines = text.splitlines()[1:]
    result = []
    fenced = False
    for line in lines:
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and re.match(r"^#{2,5} ", line):
            line = "#" + line
        result.append(line)
    return "\n".join(result).strip()


def validate_links(paths: list[Path]) -> int:
    failures = []
    count = 0
    for document in paths:
        for target in re.findall(r"\]\((/?[A-Za-z]:/[^)]+)\)", document.read_text(encoding="utf-8")):
            target = target.lstrip("/")
            match = re.fullmatch(r"(.+?):(\d+)", target)
            path = Path(match[1] if match else target)
            count += 1
            if not path.is_file():
                failures.append(f"{document.name}: missing {target}")
            elif match:
                nlines = len(path.read_text(encoding="utf-8-sig").splitlines())
                if not 1 <= int(match[2]) <= nlines:
                    failures.append(f"{document.name}: invalid line {target}")
    if failures:
        raise SystemExit("\n".join(failures))
    return count


def main() -> None:
    catalog = json.loads((HERE / "function_catalog.json").read_text(encoding="utf-8"))
    stale = [entry["path"] for entry in catalog["files"]
             if hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]]
    if stale:
        raise SystemExit("Source changed since inventory generation: " + ", ".join(stale))
    text = (HERE / "overview.md").read_text(encoding="utf-8").rstrip()
    for title, filename in CHAPTERS:
        text += "\n\n---\n\n## " + title + "\n\n"
        text += chapter_text((HERE / filename).read_text(encoding="utf-8"))
    TARGET.write_text(text + "\n", encoding="utf-8")
    paths = [TARGET, HERE / "overview.md", HERE / "function_catalog.md"]
    paths += [HERE / filename for _, filename in CHAPTERS]
    links = validate_links(paths)
    print(json.dumps({"report": str(TARGET), "lines": len(text.splitlines()),
                      "source_files_hash_verified": len(catalog["files"]),
                      "local_links_verified": links}, ensure_ascii=False))


if __name__ == "__main__":
    main()
