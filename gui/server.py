"""LS4T 可视化版本：本地 HTTP 服务、任务运行队列和静态页面。

运行：双击 gui/start.bat（或在 ls4t 根目录执行 ``python gui/server.py``），然后打开 http://127.0.0.1:8840 。
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

GUI_DIR = Path(__file__).resolve().parent
REPO_ROOT = GUI_DIR.parent
STATIC_DIR = GUI_DIR / "static"
sys.path.insert(0, str(GUI_DIR))
sys.path.insert(0, str(REPO_ROOT))

import settings as settings_module  # noqa: E402
import tasks  # noqa: E402

EVENT_PREFIX = "@@LS4T "
LOG_LINES = 400
MAX_FAILURES = 500


class Run:
    """One execution of a task in a child Python process."""

    def __init__(self, task: dict):
        self.id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.task = task
        self.state = "queued"
        self.queued = time.time()
        self.started: float | None = None
        self.finished: float | None = None
        self.total: int | None = None
        self.counts = {"done": 0, "skipped": 0, "failed": 0}
        self.current = ""
        self.failures: list[dict] = []
        self.log: deque[str] = deque(maxlen=LOG_LINES)
        self.process: subprocess.Popen | None = None
        self.cancel_requested = False
        self.log_file: Path | None = None

    def summary(self, with_log: bool = False) -> dict:
        data = {
            "id": self.id,
            "state": self.state,
            "queued": self.queued,
            "started": self.started,
            "finished": self.finished,
            "total": self.total,
            "counts": dict(self.counts),
            "current": self.current,
            "log_file": str(self.log_file) if self.log_file else None,
        }
        if with_log:
            data["log"] = list(self.log)
            data["failures"] = list(self.failures)
        return data


def conda_path(python: str) -> str:
    """PATH entries of an un-activated conda env; without them LAPACK DLLs fail to load."""
    root = Path(python).parent
    parts = [root, root / "Library" / "mingw-w64" / "bin", root / "Library" / "usr" / "bin",
             root / "Library" / "bin", root / "Scripts", root / "bin"]
    return os.pathsep.join(str(p) for p in parts if p.is_dir())


class Runner:
    """Queue of task runs; one runs at a time."""

    def __init__(self):
        self.runs: dict[str, Run] = {}  # latest run per task id
        self.queue: list[str] = []
        self.lock = threading.Lock()
        self.wakeup = threading.Event()
        threading.Thread(target=self._loop, daemon=True).start()

    def active(self, task_id: str) -> Run | None:
        run = self.runs.get(task_id)
        return run if run and run.state in ("queued", "running") else None

    def latest(self, task_id: str) -> Run | None:
        return self.runs.get(task_id)

    def submit(self, task: dict) -> Run:
        with self.lock:
            if self.active(task["id"]):
                raise ApiError("这个任务已经在运行或排队")
            run = Run(task)
            self.runs[task["id"]] = run
            self.queue.append(task["id"])
        self.wakeup.set()
        return run

    def cancel(self, task_id: str) -> bool:
        run = self.active(task_id)
        if run is None:
            return False
        run.cancel_requested = True
        if run.state == "queued":
            with self.lock:
                if task_id in self.queue:
                    self.queue.remove(task_id)
            run.state = "cancelled"
            run.finished = time.time()
            self._record(run)
        elif run.process and run.process.poll() is None:
            # Kill the whole tree: tasks use process pools.
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(run.process.pid)] if os.name == "nt" else ["kill", "-TERM", str(run.process.pid)],
                capture_output=True,
            )
        return True

    def _loop(self):
        while True:
            with self.lock:
                task_id = self.queue.pop(0) if self.queue else None
            if task_id is None:
                self.wakeup.wait(1.0)
                self.wakeup.clear()
                continue
            run = self.runs.get(task_id)
            if run and run.state == "queued":
                self._execute(run)

    def _execute(self, run: Run):
        runtime = settings_module.load()
        run.state = "running"
        run.started = time.time()
        folder = Path(run.task["output_dir"]) / "_gui"
        folder.mkdir(parents=True, exist_ok=True)
        spec = folder / f"{run.id}.json"
        spec.write_text(json.dumps({"task": run.task, "settings": runtime}, ensure_ascii=False, indent=1), encoding="utf-8")
        run.log_file = folder / f"{run.id}.log"
        env = dict(os.environ, PYTHONPATH=str(REPO_ROOT), PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        env["PATH"] = conda_path(runtime["python"]) + os.pathsep + env.get("PATH", "")
        share = Path(runtime["python"]).parent / "Library" / "share"
        if (share / "gdal").is_dir():
            env.setdefault("GDAL_DATA", str(share / "gdal"))
        if (share / "proj").is_dir():
            env.setdefault("PROJ_DATA", str(share / "proj"))
        try:
            run.process = subprocess.Popen(
                [runtime["python"], "-u", str(GUI_DIR / "worker.py"), str(spec)],
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as error:
            run.log.append(f"无法启动 Python：{error}")
            run.state = "failed"
            run.finished = time.time()
            self._record(run)
            return
        with run.log_file.open("w", encoding="utf-8") as log:
            for line in run.process.stdout:
                line = line.rstrip("\n")
                if line.startswith(EVENT_PREFIX):
                    self._event(run, line[len(EVENT_PREFIX):], log)
                    continue
                log.write(line + "\n")
                log.flush()
                run.log.append(line)
        code = run.process.wait()
        run.finished = time.time()
        run.current = ""
        if run.cancel_requested:
            run.state = "cancelled"
        elif code != 0:
            run.state = "failed"
        else:
            run.state = "done"
        self._record(run)

    @staticmethod
    def _event(run: Run, payload: str, log):
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            run.log.append(payload)
            return
        kind = event.get("type")
        if kind == "start":
            run.current = event.get("scene", "")
        elif kind == "total":
            run.total = int(event.get("total", 0))
        elif kind == "result":
            status = event.get("status", "done")
            run.counts[status if status in run.counts else "done"] += 1
            scene, message = event.get("scene", ""), event.get("message", "")
            line = f"[{status}] {scene}" + (f"  {message}" if message else "")
            run.log.append(line)
            log.write(line + "\n")
            if status == "failed" and len(run.failures) < MAX_FAILURES:
                run.failures.append({"scene": scene, "message": message})

    @staticmethod
    def _record(run: Run):
        summary = run.summary()
        summary["failures"] = run.failures
        try:
            tasks.record_run(run.task["id"], summary)
        except OSError:
            pass


RUNNER = Runner()


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _json(handler: BaseHTTPRequestHandler, payload, status: int = 200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def list_directory(path: str) -> dict:
    if not path:
        drives = [f"{letter}:\\" for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{letter}:\\").exists()]
        return {"path": "", "parent": None, "entries": [{"name": d, "path": d, "dir": True} for d in drives]}
    target = Path(path)
    if not target.is_dir():
        raise ApiError(f"目录不存在：{path}", 404)
    entries = []
    try:
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name.startswith("$"):
                continue
            entries.append({"name": item.name, "path": str(item), "dir": item.is_dir()})
            if len(entries) >= 500:
                break
    except PermissionError as error:
        raise ApiError(f"无权读取：{error}", 403) from error
    parent = str(target.parent) if target.parent != target else ""
    return {"path": str(target), "parent": parent, "entries": entries}


def _tail(path: str | None, lines: int = LOG_LINES) -> list[str]:
    if not path or not Path(path).is_file():
        return []
    with open(path, encoding="utf-8", errors="replace") as handle:
        return list(deque(handle, maxlen=lines))


def task_status(task: dict, with_log: bool = False) -> dict | None:
    """The current run if any, otherwise the last recorded run."""
    run = RUNNER.latest(task["id"])
    if run:
        return run.summary(with_log)
    last = task.get("last_run")
    if not last:
        return None
    status = dict(last)
    if with_log:
        status["log"] = [line.rstrip("\n") for line in _tail(last.get("log_file"))]
        status["failures"] = last.get("failures", [])
    else:
        status.pop("failures", None)
    return status


class Handler(BaseHTTPRequestHandler):
    server_version = "LS4T-GUI/3"

    def log_message(self, format, *args):  # quiet console
        pass

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ApiError(f"请求不是合法 JSON：{error}") from error

    def _guard_origin(self):
        # The API launches local processes: refuse cross-site browser requests.
        origin = self.headers.get("Origin")
        host = self.headers.get("Host", "")
        if origin and urlparse(origin).netloc != host:
            raise ApiError("拒绝跨站请求", 403)

    def _handle(self, action):
        try:
            action()
        except ApiError as error:
            _json(self, {"error": str(error)}, error.status)
        except FileNotFoundError as error:
            _json(self, {"error": str(error)}, 404)
        except ValueError as error:
            _json(self, {"error": str(error)}, 400)
        except Exception as error:  # surface backend errors to the page
            _json(self, {"error": f"{type(error).__name__}: {error}"}, 500)

    def do_GET(self):
        url = urlparse(self.path)
        query = {k: v[-1] for k, v in parse_qs(url.query).items()}

        def action():
            if url.path.startswith("/api/"):
                self._guard_origin()
                self._api_get(url.path, query)
            else:
                self._static(url.path)

        self._handle(action)

    def do_POST(self):
        url = urlparse(self.path)

        def action():
            self._guard_origin()
            self._api_post(url.path, self._body())

        self._handle(action)

    def _static(self, path: str):
        pages = {"/": "home.html", "/retrieval": "home.html", "/normalization": "home.html",
                 "/retrieval/surface": "workbench.html", "/retrieval/components": "workbench.html",
                 "/retrieval/batch": "index.html", "/normalization/angle": "workbench.html",
                 "/normalization/time": "normalize.html", "/normalization/space": "normalize.html",
                 "/normalization/batch": "normalize.html", "/batch.html": "index.html"}
        relative = pages.get(path.rstrip("/") or "/", path.lstrip("/"))
        target = (STATIC_DIR / relative).resolve()
        if STATIC_DIR not in target.parents or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if kind.startswith("text/") or kind in ("application/javascript",):
            kind += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _api_get(self, path: str, query: dict):
        if path == "/api/normalization/sample":
            _json(self, json.loads((GUI_DIR / "examples" / "ahi_slstr" / "normalization.json").read_text(encoding="utf-8")))
        elif path == "/api/workbench/sample":
            sample_dir = GUI_DIR / "examples" / "ahi_slstr"
            sample = json.loads((sample_dir / "sample.json").read_text(encoding="utf-8"))
            sample["route"] = "retrieval"
            sample.pop("reference_vza", None)
            sample.pop("reference_raa", None)
            for observation in sample["observations"]:
                observation["coefficient_file"] = str(sample_dir / (observation["sensor"].lower() + "_coefficients.npz"))
            _json(self, sample)
        elif path == "/api/version":
            import re
            source = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
            version = re.search(r'^version\s*=\s*"([^"]+)"', source, re.M).group(1)
            _json(self, {"application": "LS4T", "version": version})
        elif path == "/api/runtime":
            config = settings_module.load()
            _json(self, {"runtime": config, "checks": settings_module.check(config)})
        elif path == "/api/types":
            _json(self, {"types": tasks.describe_types(), "labels": tasks.LABELS})
        elif path == "/api/template":
            _json(self, {"task": tasks.template(query.get("type", "lst"))})
        elif path == "/api/tasks":
            items = []
            for task in tasks.all_tasks():
                items.append({k: task[k] for k in ("id", "type", "name", "input_dir", "output_dir", "years")} | {"status": task_status(task)})
            _json(self, {"tasks": items})
        elif path == "/api/task":
            task = tasks.get(query.get("id", ""))
            payload = {"task": task, "status": task_status(task, with_log=True)}
            if query.get("check") != "0":
                payload["check"] = tasks.check(task)
            _json(self, payload)
        elif path == "/api/fs":
            _json(self, list_directory(query.get("path", "")))
        else:
            raise ApiError("未知接口", 404)

    def _api_post(self, path: str, body: dict):
        if path in ("/api/surface/run", "/api/time/run", "/api/space/run", "/api/normalization/batch"):
            from gui.workspace_tools import run_surface, run_time, run_space, run_batch
            operation = {"/api/surface/run":run_surface, "/api/time/run":run_time,
                         "/api/space/run":run_space, "/api/normalization/batch":run_batch}[path]
            _json(self, operation(body))
        elif path == "/api/normalization/run":
            from base.normalization.workbench import normalize_observations
            _json(self, normalize_observations(body))
        elif path in ("/api/workbench/run", "/api/retrieval/run"):
            from base.known_inputs import run_workbench
            _json(self, run_workbench(body))
        elif path == "/api/runtime":
            config = settings_module.save(body.get("runtime") or {})
            _json(self, {"runtime": config, "checks": settings_module.check(config)})
        elif path == "/api/task/check":
            _json(self, tasks.check(body.get("task") or {}))
        elif path == "/api/task/save":
            identifier = body.get("id") or None
            if identifier and RUNNER.active(identifier):
                raise ApiError("任务正在运行，结束或取消后才能修改")
            task = tasks.save(body.get("task") or {}, identifier)
            _json(self, {"task": task, "check": tasks.check(task)})
        elif path == "/api/task/delete":
            identifier = body.get("id", "")
            if RUNNER.active(identifier):
                raise ApiError("任务正在运行，结束或取消后才能删除")
            tasks.delete(identifier)
            _json(self, {"ok": True})
        elif path == "/api/task/run":
            task = tasks.get(body.get("id", ""))
            check = tasks.check(task)
            if not check["ok"]:
                bad = [f"{f['label']}（{f['message']}）" for f in check["fields"].values() if not f["ok"]]
                raise ApiError("任务配置还有问题：" + "；".join(bad))
            run = RUNNER.submit(task)
            _json(self, run.summary(), 201)
        elif path == "/api/task/cancel":
            if not RUNNER.cancel(body.get("id", "")):
                raise ApiError("这个任务没有在运行")
            _json(self, {"ok": True})
        else:
            raise ApiError("未知接口", 404)


def main():
    parser = argparse.ArgumentParser(description="LS4T 可视化版本")
    parser.add_argument("--port", type=int, default=8840)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"LS4T GUI: {url}")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
