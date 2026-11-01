"""Runtime settings (Python interpreter, workers), stored in gui/local.json (not versioned)."""

from __future__ import annotations

import json
import os
from pathlib import Path

GUI_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ["LS4T_STATE_DIR"]) if os.environ.get("LS4T_STATE_DIR") else GUI_DIR
SETTINGS_FILE = STATE_DIR / "local.json"

DEFAULTS = {
    "python": os.environ.get("LS4T_PYTHON", r"C:\work\miniconda\envs\python311\python.exe"),
    "workers": max(1, min(8, (os.cpu_count() or 2) // 2)),
}

FIELDS = {
    "python": ("Python 解释器", "file"),
    "workers": ("并行进程数", "int"),
}


def load() -> dict:
    config = dict(DEFAULTS)
    if SETTINGS_FILE.is_file():
        try:
            stored = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            config.update({k: stored[k] for k in DEFAULTS if k in stored})
        except json.JSONDecodeError:
            pass
    return config


def save(values: dict) -> dict:
    config = load()
    if "python" in values:
        config["python"] = str(values["python"]).strip().strip('"')
    if "workers" in values:
        config["workers"] = max(1, int(values["workers"]))
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return config


def check(config: dict) -> dict:
    python = Path(str(config.get("python", "")))
    workers = config.get("workers")
    good_workers = isinstance(workers, int) and workers >= 1
    return {
        "python": {"label": FIELDS["python"][0], "ok": python.is_file(), "message": "" if python.is_file() else "文件不存在"},
        "workers": {"label": FIELDS["workers"][0], "ok": good_workers, "message": "" if good_workers else "需为正整数"},
    }
