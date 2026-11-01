"""Run one GUI task: ``python gui/worker.py <run.json>`` (started by gui/server.py)."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_key, "1")

EVENT_PREFIX = "@@LS4T "


def emit(event: dict) -> None:
    print(EVENT_PREFIX + json.dumps(event, ensure_ascii=False), flush=True)


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from gui import drivers

    task = spec["task"]
    print(
        f"{time.strftime('%H:%M:%S')} 开始“{task['name']}”（{task['type']}）：{task['input_dir']} → {task['output_dir']}，"
        f"年份 {', '.join(task['years'])}",
        flush=True,
    )
    started = time.time()
    drivers.RUNNERS[task["type"]](drivers.Context(spec, emit))
    print(f"{time.strftime('%H:%M:%S')} 结束，用时 {(time.time() - started) / 60:.1f} 分钟", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
