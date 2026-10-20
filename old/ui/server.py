"""LS4T 本地界面：Base（函数库浏览）+ Case（案例复制、改配置、运行）。

    python ui/server.py                  # http://127.0.0.1:8770
    python ui/server.py --port 9000 --python /path/to/env/bin/python

只监听本机；在服务器上运行时用 `ssh -L 8770:127.0.0.1:8770 host` 转发后访问。
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "base"
CASES = REPO / "cases"
INDEX = Path(__file__).with_name("index.html")
NOT_LIBRARY = {"base", "cases", "tests", "docs", "ui", "old", "archive", "build", "dist"}
CASE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$")

PYTHON = sys.executable
RUNS: dict[str, dict] = {}
RUNS_LOCK = threading.Lock()


class ApiError(Exception):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def resolve(relative: str, *, under: Path = REPO) -> Path:
    path = (REPO / relative).resolve()
    if not path.is_relative_to(under.resolve()):
        raise ApiError(f"路径不在 {rel(under) if under != REPO else '项目'} 内: {relative}", HTTPStatus.FORBIDDEN)
    return path


def python_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        parts = path.relative_to(root).parts
        if any(p == "__pycache__" or p == "logs" or p.startswith(".") for p in parts):
            continue
        yield path


def parse(source: str) -> ast.Module | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


# ---------------------------------------------------------------- base


def describe_function(node, source: str) -> dict:
    args = ast.unparse(node.args) if not isinstance(node, ast.ClassDef) else ""
    doc = ast.get_docstring(node) or ""
    return {
        "kind": "class" if isinstance(node, ast.ClassDef) else "def",
        "name": node.name,
        "signature": f"{node.name}({args})" if args or not isinstance(node, ast.ClassDef) else node.name,
        "doc": doc.strip().splitlines()[0] if doc.strip() else "",
        "line": node.lineno,
        "end": node.end_lineno,
    }


def base_modules() -> list[dict]:
    modules = []
    for path in python_files(BASE):
        source = read_text(path)
        tree = parse(source)
        items = []
        if tree is not None:
            items = [
                describe_function(n, source)
                for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_")
            ]
        doc = (ast.get_docstring(tree) or "").strip().splitlines() if tree else []
        modules.append({
            "path": rel(path),
            "module": rel(path)[:-3].replace("/", "."),
            "doc": doc[0] if doc else "",
            "items": items,
            "error": tree is None,
        })
    return modules


# ---------------------------------------------------------------- case


def is_main_guard(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
    )


def is_script(tree: ast.Module | None) -> bool:
    if tree is None:
        return False
    for node in tree.body:
        if is_main_guard(node) or isinstance(node, (ast.For, ast.While, ast.With)):
            return True
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = ast.unparse(node.value.func)
            if not func.startswith("warnings."):
                return True
    return False


def config_nodes(tree: ast.Module):
    """顶层与 `if __name__ == "__main__":` 内、值为字面量的赋值，即脚本的配置项。"""
    bodies = [tree.body] + [n.body for n in tree.body if is_main_guard(n)]
    for body in bodies:
        for node in body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name, value = node.targets[0].id, node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                name, value = node.target.id, node.value
            else:
                continue
            try:
                ast.literal_eval(value)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                continue
            yield name, value


def script_info(path: Path) -> dict:
    source = read_text(path)
    tree = parse(source)
    config = []
    if tree is not None:
        config = [
            {"name": name, "line": value.lineno, "text": ast.get_source_segment(source, value)}
            for name, value in config_nodes(tree)
        ]
    return {
        "path": rel(path),
        "source": source,
        "config": config,
        "parse_error": tree is None,
        "in_cases": path.is_relative_to(CASES),
        "case": path.relative_to(CASES).parts[0] if path.is_relative_to(CASES) else None,
    }


def library_groups() -> list[dict]:
    groups = []
    for directory in sorted(p for p in REPO.iterdir() if p.is_dir()):
        name = directory.name
        if name in NOT_LIBRARY or name.startswith((".", "_")) or name.endswith(".egg-info"):
            continue
        scripts = [rel(p) for p in python_files(directory) if is_script(parse(read_text(p)))]
        if scripts:
            groups.append({"name": name, "scripts": scripts})
    return groups


def case_list() -> list[dict]:
    cases = []
    if not CASES.is_dir():
        return cases
    for directory in sorted(p for p in CASES.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
        readme = directory / "README.md"
        cases.append({
            "name": directory.name,
            "readme": read_text(readme) if readme.is_file() else "",
            "scripts": [rel(p) for p in python_files(directory)],
        })
    return cases


def create_case(name: str) -> Path:
    if not CASE_NAME.match(name or ""):
        raise ApiError("案例名只能包含字母、数字、下划线、点和短横线，例如 heihe_2022_slstr")
    directory = CASES / name
    if not directory.exists():
        directory.mkdir(parents=True)
        (directory / "README.md").write_text(
            f"# {name}\n\n- 内容：\n- 运行顺序：\n- 结果位置：\n", encoding="utf-8"
        )
    return directory


def copy_script(source: str, case: str, overwrite: bool) -> str:
    src = resolve(source)
    if src.suffix != ".py" or not src.is_file():
        raise ApiError(f"不是脚本文件: {source}")
    target = create_case(case) / src.name
    if target.exists() and not overwrite:
        raise ApiError(f"{rel(target)} 已存在", HTTPStatus.CONFLICT)
    shutil.copy2(src, target)
    return rel(target)


def save_config(path: str, values: list[dict]) -> dict:
    target = resolve(path, under=CASES)
    source = read_text(target)
    tree = parse(source)
    if tree is None:
        raise ApiError("脚本有语法错误，不能在界面中修改配置")
    nodes = {(value.lineno, name): value for name, value in config_nodes(tree)}
    data = source.encode("utf-8")
    line_starts = [0]
    for line in data.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))

    edits = []
    for item in values:
        node = nodes.get((int(item["line"]), item["name"]))
        if node is None:
            raise ApiError(f"找不到配置项 {item['name']}（第 {item['line']} 行），请刷新后重试")
        text = str(item["text"]).strip()
        try:
            ast.literal_eval(text)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            raise ApiError(f"{item['name']} 的值不是合法的 Python 字面量: {text}")
        if "\n" in text and node.lineno == node.end_lineno:
            raise ApiError(f"{item['name']} 的值不能换行")
        start = line_starts[node.lineno - 1] + node.col_offset
        end = line_starts[node.end_lineno - 1] + node.end_col_offset
        edits.append((start, end, text.encode("utf-8")))

    for start, end, text in sorted(edits, reverse=True):
        data = data[:start] + text + data[end:]
    new_source = data.decode("utf-8")
    if parse(new_source) is None:
        raise ApiError("修改后脚本无法解析，未保存")
    target.write_text(new_source, encoding="utf-8")
    return script_info(target)


# ---------------------------------------------------------------- runs


def start_run(path: str, python: str | None) -> dict:
    script = resolve(path, under=CASES)
    if script.suffix != ".py" or not script.is_file():
        raise ApiError(f"不是脚本文件: {path}")
    interpreter = (python or PYTHON).strip()
    case_dir = CASES / script.relative_to(CASES).parts[0]
    log_dir = case_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = log_dir / f"{script.stem}_{stamp}.log"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(REPO), os.environ.get("PYTHONPATH")])),
               PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    handle = log.open("wb")
    try:
        process = subprocess.Popen([interpreter, str(script)], cwd=REPO, env=env,
                                   stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    except OSError as exc:
        handle.close()
        raise ApiError(f"无法启动 {interpreter}: {exc}")
    run = {
        "id": f"{stamp}_{process.pid}",
        "path": rel(script),
        "python": interpreter,
        "log": rel(log),
        "start": time.time(),
        "end": None,
        "status": "running",
        "returncode": None,
    }
    with RUNS_LOCK:
        RUNS[run["id"]] = run | {"_process": process}

    def wait():
        code = process.wait()
        handle.close()
        with RUNS_LOCK:
            entry = RUNS[run["id"]]
            entry.update(end=time.time(), returncode=code,
                         status="stopped" if entry["status"] == "stopping" else ("done" if code == 0 else "failed"))

    threading.Thread(target=wait, daemon=True).start()
    return public_run(RUNS[run["id"]])


def public_run(run: dict) -> dict:
    return {k: v for k, v in run.items() if not k.startswith("_")}


def stop_run(run_id: str) -> dict:
    with RUNS_LOCK:
        run = RUNS.get(run_id)
        if run is None:
            raise ApiError("没有这个运行记录", HTTPStatus.NOT_FOUND)
        if run["status"] == "running":
            run["status"] = "stopping"
            run["_process"].terminate()
        return public_run(run)


def read_log(run_id: str, offset: int) -> dict:
    with RUNS_LOCK:
        run = RUNS.get(run_id)
    if run is None:
        raise ApiError("没有这个运行记录", HTTPStatus.NOT_FOUND)
    path = REPO / run["log"]
    with path.open("rb") as handle:
        handle.seek(offset)
        chunk = handle.read(256_000)
    return {"text": chunk.decode("utf-8", errors="replace"), "offset": offset + len(chunk), "run": public_run(run)}


# ---------------------------------------------------------------- http


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def dispatch(self, method: str):
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if method == "GET" and url.path == "/":
                body = INDEX.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if method == "POST" and self.headers.get("Origin") not in (None, f"http://{self.headers.get('Host')}"):
                raise ApiError("拒绝跨站请求", HTTPStatus.FORBIDDEN)
            route = (method, url.path)
            if route == ("GET", "/api/info"):
                result = {"repo": str(REPO), "python": PYTHON}
            elif route == ("GET", "/api/base/modules"):
                result = base_modules()
            elif route == ("GET", "/api/source"):
                path = resolve(query.get("path", ""))
                if path.suffix != ".py" or not path.is_file():
                    raise ApiError("不是脚本文件", HTTPStatus.NOT_FOUND)
                result = script_info(path)
            elif route == ("GET", "/api/case/list"):
                result = {"library": library_groups(), "cases": case_list()}
            elif route == ("POST", "/api/case/create"):
                result = {"path": rel(create_case(self.body().get("name", "")))}
            elif route == ("POST", "/api/case/copy"):
                data = self.body()
                result = {"path": copy_script(data.get("path", ""), data.get("case", ""), bool(data.get("overwrite")))}
            elif route == ("POST", "/api/case/config"):
                data = self.body()
                result = save_config(data.get("path", ""), data.get("values", []))
            elif route == ("POST", "/api/case/run"):
                data = self.body()
                result = start_run(data.get("path", ""), data.get("python"))
            elif route == ("GET", "/api/case/runs"):
                with RUNS_LOCK:
                    result = [public_run(r) for r in sorted(RUNS.values(), key=lambda r: r["start"], reverse=True)]
            elif route == ("POST", "/api/case/stop"):
                result = stop_run(self.body().get("id", ""))
            elif route == ("GET", "/api/case/log"):
                result = read_log(query.get("id", ""), int(query.get("offset", 0)))
            else:
                raise ApiError("not found", HTTPStatus.NOT_FOUND)
            self.send_json(result)
        except ApiError as exc:
            self.send_json({"error": str(exc)}, exc.status)
        except Exception as exc:  # noqa: BLE001 - surface unexpected errors to the page
            self.send_json({"error": f"{type(exc).__name__}: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")


def main() -> None:
    global PYTHON
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--python", default=sys.executable, help="运行案例脚本用的解释器（默认当前解释器）")
    args = parser.parse_args()
    PYTHON = args.python
    # Windows 的 SO_REUSEADDR 允许两个进程绑定同一端口，端口被占时会静默失效
    ThreadingHTTPServer.allow_reuse_address = os.name != "nt"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as exc:
        raise SystemExit(f"端口 {args.port} 不可用（{exc}），换一个：--port 8771")
    print(f"LS4T UI: http://127.0.0.1:{args.port}  (repo={REPO})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
