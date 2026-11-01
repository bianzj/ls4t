"""Build a read-only AST inventory of current LS4T source and lexical test links.

Only the generated JSON and Markdown files next to this script are written.
The index includes functions, methods and nested objective functions, not just
public APIs. Call/test mentions are static evidence, not execution coverage.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EXCLUDED = {"_archive", "outputs", "logs", "runs", "data", "__pycache__", ".case-state", ".git"}


def source_paths():
    for directory in (ROOT / "base", ROOT / "cases", ROOT / "tests/examples"):
        for path in sorted(directory.rglob("*.py")):
            if not EXCLUDED.intersection(path.relative_to(directory).parts):
                yield path


def definitions(tree, path, source):
    items = []

    def walk(node, prefix="", parent_kind="module"):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                walk(child, prefix + child.name + ".", "class")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                signature = f"{prefix}{child.name}({ast.unparse(child.args)})"
                if child.returns is not None:
                    signature += " -> " + ast.unparse(child.returns)
                calls = sorted({ast.unparse(call.func) for call in ast.walk(child)
                                if isinstance(call, ast.Call) and len(ast.unparse(call.func)) < 120})
                body_hash = hashlib.sha256(ast.dump(ast.Module(body=child.body, type_ignores=[]),
                    include_attributes=False).encode()).hexdigest()
                items.append({"file": path.relative_to(ROOT).as_posix(), "name": child.name,
                    "qualified_name": prefix + child.name, "line": child.lineno,
                    "end_line": child.end_lineno, "signature": signature,
                    "kind": "method" if parent_kind == "class" else "nested" if parent_kind == "function" else "function",
                    "docstring": ast.get_docstring(child) or "", "calls": calls,
                    "body_sha256": body_hash})
                walk(child, prefix + child.name + ".", "function")
            else:
                walk(child, prefix, parent_kind)

    walk(tree)
    return items


def main():
    files, functions, errors = [], [], []
    tests = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        tests.append((path, path.read_text(encoding="utf-8-sig")))
    for path in source_paths():
        try:
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeError) as error:
            errors.append({"file": str(path.relative_to(ROOT)), "error": str(error)})
            continue
        items = definitions(tree, path, source)
        for item in items:
            pattern = re.compile(r"\b" + re.escape(item["name"]) + r"\b")
            item["test_mentions"] = [{"file": test.relative_to(ROOT).as_posix(),
                "line": text[:match.start()].count("\n") + 1}
                for test, text in tests if (match := pattern.search(text))]
        functions.extend(items)
        files.append({"path": path.relative_to(ROOT).as_posix(), "lines": len(source.splitlines()),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "definitions": len(items)})
    duplicates = defaultdict(list)
    for item in functions:
        duplicates[item["body_sha256"]].append(f"{item['file']}:{item['line']}:{item['qualified_name']}")
    duplicate_groups = [group for group in duplicates.values() if len(group) > 1]
    summary = {"files": len(files), "definitions": len(functions),
               "by_root": dict(Counter(item["file"].split('/')[0] for item in functions)),
               "by_kind": dict(Counter(item["kind"] for item in functions)),
               "exact_body_duplicate_groups": len(duplicate_groups), "parse_errors": len(errors)}
    result = {"root": str(ROOT), "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "scope": ["base/**/*.py", "cases/**/*.py", "tests/examples/**/*.py"],
              "excluded_directory_names": sorted(EXCLUDED),
              "warning": "Definitions are not independent methods. Duplicate bodies and lexical test mentions are not scientific validation.",
              "summary": summary, "files": files, "functions": functions,
              "exact_body_duplicates": duplicate_groups, "parse_errors": errors}
    (OUT / "function_catalog.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# LS4T 函数级源码索引", "", "由 `build_inventory.py` 对当前工作区做 AST 解析生成。",
        "包含函数、类方法和嵌套目标函数；函数数量不等于独立算法数量。排除归档、数据与生成输出。",
        "测试引用只是同名符号的静态文本命中，可能同名误配；不能作为覆盖率或独立精度证明。",
        "JSON 另含调用符号、源码哈希、完整 docstring 和重复函数体分组。", "",
        "```json", json.dumps(summary, ensure_ascii=False, indent=2), "```", ""]
    grouped = defaultdict(list)
    for item in functions:
        grouped[item["file"]].append(item)
    for path in files:
        name = path["path"]
        lines.extend([f"## {name}", "", f"源码：[打开文件]({(ROOT/name).as_posix()})；{path['lines']} 行，{path['definitions']} 个定义。", ""])
        for item in grouped[name]:
            doc = " ".join(item["docstring"].splitlines())[:260] or "无 docstring；算法解释见人工审阅章节。"
            lines.extend([f"### `{item['qualified_name']}`", "", "```python", item["signature"], "```", "",
                f"定义类型：{item['kind']}；[源码第 {item['line']} 行]({(ROOT/name).as_posix()}:{item['line']})。", "", doc, ""])
            if item["test_mentions"]:
                lines.append("同名测试引用：" + "、".join(f"[{ref['file']}:{ref['line']}]({(ROOT/ref['file']).as_posix()}:{ref['line']})" for ref in item["test_mentions"]))
                lines.append("")
    if errors:
        lines.extend(["## 未成功解析的文件", "", "```json", json.dumps(errors, ensure_ascii=False, indent=2), "```"])
    (OUT / "function_catalog.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
