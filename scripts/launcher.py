"""Launch the bundled LS4T web workbench with its own Python runtime."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="LS4T workbench")
    parser.add_argument("--port", type=int, default=8840)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()
    root = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
    app = root / "app" if (root / "app").is_dir() else root
    if args.version:
        import re
        match = re.search(r'^version\s*=\s*"([^"]+)"', (app / "pyproject.toml").read_text(encoding="utf-8"), re.M)
        print("LS4T " + match.group(1))
        return 0
    python = root / "runtime" / "python.exe"
    if not python.is_file():
        raise SystemExit("Bundled runtime/python.exe is missing. Use gui/start.bat for a source checkout.")
    state = args.state_dir or Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LS4T"
    state.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "GDAL_DATA", "PROJ_LIB", "PROJ_DATA"):
        env.pop(key, None)
    env.update(LS4T_STATE_DIR=str(state.resolve()), LS4T_PYTHON=str(python), PYTHONNOUSERSITE="1", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    env["PATH"] = str(python.parent) + os.pathsep + str(python.parent / "Library" / "bin") + os.pathsep + env.get("PATH", "")
    cmd = [str(python), "-I", "-B", str(app / "gui" / "server.py"), "--port", str(args.port)]
    if args.no_browser:
        cmd.append("--no-browser")
    print(f"LS4T: http://127.0.0.1:{args.port}\nClose this window or press Ctrl+C to stop the workbench.", flush=True)
    process = subprocess.Popen(cmd, cwd=str(app), env=env)
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
