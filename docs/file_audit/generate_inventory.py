"""Read-only project inventory: AST references, exact duplicates, and per-file decisions.

Run with Python 3.11. Only audit reports are written; scientific modules are never imported.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tokenize
import tomllib

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/file_audit"
REPORTS = {"docs/FILE_AUDIT.md"} | {
    "docs/file_audit/" + name for name in (
        "inventory.json", "active_files.md", "historical_files.md", "test_data_files.md",
        "local_files.md", "duplicates.md", "validation.txt",
    )
}
BROKEN_ROOTS = ("cases/slstr/heihe/study_area_2022/", "cases/slstr/europe_south_africa/scene_first_migrated/")
LABELS = {
    "core": "核心必需", "feature": "对应功能必需", "case": "案例按需保留",
    "comparison": "对照方法；可移出主视图", "broken": "失效旧快照；建议归档",
    "verification": "测试/基准必需", "documentation": "维护说明/配置",
    "tool": "辅助工具；按需保留", "history": "历史追溯；非当前运行必需",
    "duplicate": "历史相同副本；精简候选", "generated": "可再生成",
    "environment": "本地环境；非交付源码", "editor": "本机编辑器配置",
    "lock": "临时锁文件；关闭应用后清理",
}
CORE = {
    "__init__": "公共 API 导出及包初始化；导入子模块时也会执行",
    "calibration": "分裂窗系数模型构造、保存与读取",
    "data": "标准温度产品 NPZ 序列化；仍由测试和高层产品使用",
    "dates": "公历日期与年积日转换",
    "dual_thermal": "MODIS/VIIRS/AHI/ASTER 共用双热通道产品和处理基础",
    "files": "文件检索、NPZ/HDF/NetCDF/栅格及文本读写兼容函数",
    "fitting": "AATSR 线性最小二乘与 sklearn 拟合",
    "kernel": "MSG 站点角度核、DTC/DTCRL 模型及拟合代价函数",
    "lsct": "组分温度辐射域反演、窗口参考解及历史接口",
    "lsct_window": "历史 AATSR/SLSTR 窗口约束反演；base.lsct 仍转出其函数",
    "lst": "八特征广义分裂窗 LST 模型与反演",
    "metrics": "验证 RMSE、R² 等统计量",
    "parameters": "检查案例是否显式传入路径、年份等必需参数",
    "product": "产品层级、元数据、温度变量与文件命名契约",
    "quality": "共享质量标志位及有效性判断",
    "radiometry": "显式单位 Planck 正反变换、温度解码及历史兼容接口",
    "raster": "具名波段 GeoTIFF 读写与 VRT 地理定位",
    "spatial": "同网格裁剪、拼接、投影及历史几何辅助函数",
}
STAGES = {
    "data": "数据模型、单景读取及数据产品写入", "extract": "观测提取",
    "unzip": "原始归档解压", "project": "投影到显式目标网格",
    "region": "研究区裁剪/拼接，支持反演前或反演后处理",
    "merge": "同次获取影像拼接", "lst": "地表温度反演",
    "lsct": "组分温度反演", "reconstruct": "几何和质量重建",
    "grid": "SLSTR 1 km 网格常量", "scene_skip": "读取案例的无贡献景清单",
}
SPECIAL = {
    "README.md": "项目结构、案例调用、产品层级和 MSG 测试样例总入口",
    "pyproject.toml": "构建/安装、依赖声明、包发现与 pytest 配置",
    ".gitignore": "缓存、构建产物和案例结果的版本控制排除规则",
    ".gitattributes": "Git 文件属性及换行处理规则",
    "cases/catalog.toml": "案例状态、入口及归档登记；已退出失效 SLSTR 旧入口",
    "cases/projects.toml": "独立运行项目的来源版本与迁移索引；当前状态以 catalog 为准",
    "tests/examples/msg_evo_sample.py": "EVO 2017-10 真实 MSG 裁剪、原编码解码及两/三组分参考反演",
    "docs/file_audit/generate_inventory.py": "生成本次逐文件清单；只读 AST/哈希，不执行案例",
    "cases/msg/msg_project_hdf5.py": "统一 LSASAF EURO/IODC LST 与 LAI 的 HDF5→GeoTIFF 投影实现",
    "cases/msg/msg_project_euro.py": "保留旧 EURO LST 命令入口；委托统一投影函数",
    "cases/msg/msg_project_euro_lai.py": "保留旧 EURO LAI 命令入口；委托统一投影函数",
    "cases/msg/msg_project_iodc.py": "保留旧 IODC LST 命令入口；委托统一投影函数",
    "cases/msg/msg_lsct_iter.py": "当前本仓库正式 MSG 约束/先验组分反演案例入口",
    "cases/msg/msg_lsct_2c_full.py": "两组分窗口最小二乘对照方法",
    "cases/msg/msg_lsct_3c_full.py": "三组分无约束窗口最小二乘基线",
    "cases/msg/msg_lsct_3c_2stage_full.py": "三组分两阶段无约束对照方法",
    "cases/msg/msg_lsct_3c_constrained_full.py": "三组分全向量化约束对照方法",
    "cases/msg/msg_lsct_3c_show_full.py": "组分反演及逐景诊断出图对照入口",
    "cases/msg/msg_lst_fit.py": "备用自研 MSG 分裂窗 LST；使用官方 MLST 时无需执行",
    "cases/msg/msg_smoke_test.py": "隔离重建一个真实时次并比较历史产品；需要外部数据",
    "cases/msg/msg_download.py": "下载官方 LSASAF LAI/MDST 产品；输入已准备时可跳过下载",
    "cases/msg/msg_extract_euro.py": "EURO native 观测提取；主要服务自研 LST 备用链",
    "cases/msg/msg_extract_iodc.py": "IODC native 观测提取；主要服务自研 LST 备用链",
    "cases/msg/msg_site_extract_csv.py": "读取历史 MLST_COMPONENT2 并导出站点 CSV；与当前正式输出目录不同",
    "cases/msg/msg_site_extract_lai.py": "从每日 LAI 产品抽取站点输入",
    "cases/msg/msg_site_extract_lst.py": "从 MSG LST/观测角抽取站点输入",
    "cases/msg/msg_site_extract_static.py": "抽取站点静态地类、发射率、位置和角度",
    "cases/msg/msg_site_extract_series.py": "从归档 LSCT 抽取跨季节的站点时间序列",
    "cases/msg/msg_site_fit.py": "站点 DTC/DTCRL/DTCLSFRL 日变化及角度模型拟合",
    "cases/msg/msg_site_stats.py": "站点结果汇总统计",
    "cases/msg/msg_site_validate.py": "组分温度与站点实测匹配、过滤及统计",
    "cases/msg/msg_site_validate_multisite.py": "ICOS 多站点匹配与质量筛选验证",
    "cases/msg/msg_site_repro_lst.py": "复现 EVO LST 历史验证并对照基准 CSV",
    "cases/msg/msg_site_repro_lsct.py": "复现 EVO 组分温度与日变化验证",
    "cases/aatsr/aatsr_001deg_stats.py": "生成/续算 AATSR 0.01 度逐日与逐月统计产品",
    "cases/aatsr/aatsr_monthly_3files.py": "将昼夜土壤、植被及天底温度汇总为三个逐月时间栈",
    "cases/aatsr/aatsr_lsct_latlon.py": "AATSR 按经纬度/列分块的组分温度实现",
    "cases/aatsr/aatsr_lsct_ndvi.py": "使用 NDVI 条件的 AATSR 组分温度窗口/线性方案",
    "cases/aatsr/aatsr_lsct_v31.py": "AATSR v3.1 两组分反演变体；不是同名文件副本",
    "cases/aatsr/aatsr_site_inv_bayes.py": "AATSR 站点贝叶斯/岭回归组分温度方案",
    "cases/aatsr/aatsr_site_series.py": "AATSR 站点长期变化、季节性与去季节趋势分析",
    "cases/aatsr/util_aatsr.py": "AATSR 案例专用辅助数据和站点读取、反演支持函数",
    "cases/slstr/slstr_data_scene.py": "SLSTR 逐景数据重整基础入口",
    "cases/slstr/slstr_data_scene_origin.py": "SLSTR 原始轨道逐景数据重整入口；逐年驱动调用它",
    "cases/slstr/slstr_data_scene_latlon.py": "SLSTR 逐景重整并保留/处理经纬度的变体",
    "cases/slstr/slstr_data_scene_years.py": "逐年调用 origin 数据提取脚本，支持已有输出恢复",
    "cases/slstr/slstr_data_batch.py": "SLSTR 批量并行重整与投影；与单景入口有不同执行组织",
    "cases/slstr/slstr_lsct2_scene_parallel.py": "并行续算缺失的逐景两组分 LSCT 产品",
    "cases/slstr/slstr_lst_scene_parallel.py": "并行执行逐景双视角 LST 反演",
    "cases/slstr/slstr_daily_mosaic_scene.py": "读取案例区域窗口与配置，汇总逐景 LST/LSCT2 日产品",
    "cases/slstr/slstr_monthly_paired.py": "读取案例配置生成逐月严格配对 LST/LSCT2 产品",
    "cases/slstr/slstr_scene_coverage.py": "按地理定位抽样标记不贡献研究区的景，生成跳过清单",
    "cases/msg/Validation_Stats_Nadir_vs_Obs.csv": "历史 EVO LST 验证对照表；保留一份可追溯基准",
    "old/data_satellite/MSG_data_angle.py": "历史 MSG 静态角度生成脚本；当前角度资产追溯线索，优先保留",
    "old/data_satellite/MSG_data_angle_cut.py": "历史 MSG 静态角度裁剪脚本；当前角度资产追溯线索，优先保留",
    "old/backup/backup.rar": "旧源码压缩备份；本次未解包，不能判定与可见源码完全等价",
    "old/ShIP备忘录.docx": "历史研究备忘录；未进行正文逐段审阅，不能判为无价值副本",
    "old/ui/server.py": "已移出的旧交互界面后端，不是当前函数库运行入口",
    "old/ui/index.html": "已移出的旧交互界面页面，不是当前函数库运行入口",
}


for _old, _new in {
    "msg_lsct_2c_full.py": "msg_lsct_2c_window.py",
    "msg_lsct_3c_full.py": "msg_lsct_3c_window.py",
    "msg_lsct_3c_2stage_full.py": "msg_lsct_3c_two_stage.py",
    "msg_lsct_3c_constrained_full.py": "msg_lsct_3c_constrained.py",
    "msg_lsct_3c_show_full.py": "msg_lsct_3c_diagnostics.py",
}.items():
    SPECIAL["cases/msg/experiments/" + _new] = SPECIAL["cases/msg/" + _old]


def generated(path):
    parts = Path(path).parts
    return ("__pycache__" in parts or ".pytest_cache" in parts or
            any(p.endswith(".egg-info") for p in parts) or
            path.startswith("tests/outputs/") or
            (path.startswith("cases/") and any(p in parts for p in ("outputs", "runs", "logs", ".case-state"))) or
            Path(path).suffix in (".pyc", ".pyo", ".nbc", ".nbi"))


def historical(path):
    return path.startswith(("old/", "cases/_archive/", *BROKEN_ROOTS))


def purpose(path, info):
    p = Path(path)
    if path in SPECIAL:
        return SPECIAL[path]
    if path.startswith(".venv/"):
        return "本地 Python 3.14 虚拟环境组件：" + p.name + "；本次验证使用外部 Conda python311"
    if "__pycache__" in p.parts or p.suffix in (".pyc", ".pyo", ".nbc", ".nbi"):
        return "Python/Numba 编译缓存：" + p.name
    if ".pytest_cache" in p.parts:
        return "pytest 本机运行状态缓存：" + p.name
    if any(x.endswith(".egg-info") for x in p.parts):
        return "安装生成的包元数据：" + p.name
    if p.name.startswith("~$"):
        return "Office 打开的历史文档对应锁/所有者记录"
    if path.startswith("tests/data/msg_evo_"):
        if "/PRODUCTS/" in path:
            variable = "每日 LAI" if "_LAI_" in p.name else "逐小时 LST"
            sensor = "IODC" if "MSG-IODC" in p.name else "EURO"
            return f"EVO 10×10 {sensor} {variable}，UTC {p.stem.rsplit('_', 1)[-1]}；原编码真实输入"
        if "/Static/" in path:
            return "EVO 10×10 原编码静态观测角：" + p.stem
        if p.name == "manifest.json":
            return "样例时间轴、网格、文件哈希和单位约定"
        if p.name == "sources.json":
            return "逐原文件路径、裁剪字节哈希和 HDF5 定标属性"
        return "反演必需的样例派生辅助量：" + p.stem
    if path.startswith("tests/outputs/"):
        return "可由对应测试/样例重新生成的诊断或审阅输出：" + p.name
    if path.startswith("base/") and len(p.parts) == 2 and p.suffix == ".py":
        return CORE.get(p.stem, "公共库模块：" + p.stem)
    if p.name == "__init__.py":
        return "包初始化/公共符号导出：" + p.parent.as_posix() + "；同名或空文件不代表可删"
    if p.name == "run_standard_stage.py":
        return "从当前案例目录加载配置、动态调用 base 阶段函数；模板副本仍依赖所在路径"
    if p.name == "new_case.py":
        return "根据模板生成传感器/研究区案例目录"
    if p.name == "audit_cases.py":
        return "核对案例登记、目录和机器配置；不验证科学入口能否导入"
    if p.name == "case.toml":
        return "所在案例的传感器、时期、处理模式和入口配置"
    if "machines" in p.parts and p.suffix == ".toml":
        return "机器路径与运行资源配置：" + p.stem + "；仅该机器运行时必需"
    if p.suffix == ".toml":
        return "案例/生产目录与阶段配置：" + p.stem
    if p.suffix == ".geojson":
        return "研究区边界/空间窗口：" + p.stem
    if p.suffix == ".md":
        return "所在模块的用途、运行约定或迁移说明；标题：" + (info.get("heading") or p.stem)
    if p.suffix == ".py":
        if p.name.startswith("test_"):
            return "自动化回归测试：" + p.stem.removeprefix("test_")
        if path.startswith("base/") and len(p.parts) == 3:
            sensor, name = p.parts[1], p.stem
            if name.startswith(sensor + "_"):
                return sensor.upper() + " " + STAGES.get(name[len(sensor) + 1:], name)
            lookup = {
                "rt": {"gap": "冠层间隙概率", "hotspot": "热点/双向间隙", "hom": "均匀冠层场景模型", "emissivity": "组分发射率", "radiance": "组分辐射", "scatter": "多次散射", "proportion": "可见组分比例", "physicsF": "冠层旧 Planck 接口；参数顺序与新接口不同"},
                "normalization": {"angle": "角度归一化", "time": "地方太阳时归一化", "space": "空间聚合与质量合并", "sensor": "跨传感器校准", "profile": "归一化基准契约", "fusion": "同基准 L3N 融合"},
                "composite": {"temporal": "时间合成", "monthly_paired": "严格成对 LST/LSCT 月合成"},
                "applications": {"tvdi": "温度植被干旱指数应用"},
            }
            if sensor in lookup and name in lookup[sensor]:
                return lookup[sensor][name]
        words = [("lsct", "组分温度"), ("lst", "地表温度"), ("lai", "叶面积指数"), ("tcw", "大气水汽"), ("era5", "ERA5 辅助数据"), ("download", "下载"), ("unzip", "解压"), ("project", "投影"), ("proj", "投影"), ("extract", "抽取"), ("data", "数据预处理"), ("site", "站点"), ("val", "验证"), ("fit", "拟合"), ("plot", "绘图"), ("monthly", "月合成"), ("daily", "日合成"), ("scene", "逐景"), ("area", "研究区"), ("batch", "批处理"), ("parallel", "并行"), ("coverage", "覆盖率"), ("years", "逐年恢复运行")]
        tags = list(dict.fromkeys(v for k, v in words if k in p.stem.lower()))
        return ("历史" if historical(path) else "案例") + "脚本：" + ("、".join(tags) or p.stem)
    if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".svg"):
        return "历史图件/报告资产：" + p.name + "；未进行图像或逐页内容审阅"
    if p.suffix.lower() in (".csv", ".txt", ".json", ".npz", ".tif", ".h5", ".nc"):
        return "配置/数据/结果资产：" + p.name + "；仅凭扩展名不能判断可再生成"
    if p.suffix == ".sh":
        return "Shell 阶段运行入口：" + p.stem
    if ".idea" in p.parts or ".vscode" in p.parts:
        return "本机 IDE 设置：" + p.name
    return "历史或辅助资产：" + p.name + "；未验证替代来源，建议保留追溯"


def category(path):
    p = Path(path)
    if path.startswith(".venv/"):
        return "environment"
    if generated(path):
        return "generated"
    if p.name.startswith("~$"):
        return "lock"
    if ".idea" in p.parts or ".vscode" in p.parts:
        return "editor"
    if path.startswith(BROKEN_ROOTS):
        return "broken"
    if historical(path):
        return "history"
    if path.startswith("tests/") or path == "cases/msg/Validation_Stats_Nadir_vs_Obs.csv":
        return "verification"
    if path.startswith("base/templates/") or path == "docs/file_audit/generate_inventory.py":
        return "tool"
    if p.suffix == ".md":
        return "documentation"
    if path.startswith("base/"):
        return "core" if len(p.parts) == 2 else "feature"
    if path.startswith("cases/msg/experiments/") and p.suffix == ".py":
        return "comparison"
    if path.startswith("cases/") and p.suffix in (".py", ".sh", ".geojson"):
        return "case"
    return "documentation"


def scan():
    rows, trees, texts = {}, {}, {}
    for directory, folders, files in os.walk(ROOT, followlinks=False):
        folders[:] = [f for f in folders if f != ".git"]
        for name in files:
            p = Path(directory) / name
            rel = p.relative_to(ROOT).as_posix()
            if rel in REPORTS:
                continue
            raw = p.read_bytes()
            row = {"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                   "category": category(rel), "symbols": [], "imports": [], "referenced_by": [],
                   "entry_registered": False, "missing_base_modules": []}
            rows[rel] = row
            if not rel.startswith(".venv/") and not generated(rel):
                if p.suffix == ".py":
                    try:
                        with tokenize.open(p) as f:
                            source = f.read()
                        texts[rel] = source
                        tree = ast.parse(source, filename=rel)
                        trees[rel] = tree
                        row["docstring"] = (ast.get_docstring(tree) or "").split("\n\n")[0][:450]
                        row["symbols"] = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))]
                    except (SyntaxError, UnicodeError, LookupError) as exc:
                        row["parse_error"] = str(exc)
                elif p.suffix in (".md", ".toml", ".sh", ".json"):
                    source = raw.decode("utf-8-sig", errors="replace")
                    texts[rel] = source
                    if p.suffix == ".md":
                        row["heading"] = next((l.lstrip("# ") for l in source.splitlines() if l.startswith("#")), "")
            row["purpose"] = purpose(rel, row)
    return rows, trees, texts


def references(rows, trees, texts):
    modules = {}
    for path in trees:
        name = path[:-3].replace("/", ".")
        if name.endswith(".__init__"):
            name = name[:-9]
        modules[name] = path
    def resolve(name, owner):
        candidates = [name, str(Path(owner).parent / name.replace(".", "/")).replace("\\", "/").replace("/", ".")]
        return next((modules[x] for x in candidates if x in modules), None)
    for owner, tree in trees.items():
        targets = set()
        package = owner[:-3].replace("/", ".").split(".")[:-1]
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [x.name for x in node.names]
            elif isinstance(node, ast.ImportFrom):
                prefix = node.module or ""
                if node.level:
                    prefix = ".".join(package[:len(package) - node.level + 1] + ([prefix] if prefix else []))
                names = [prefix] + [prefix + "." + x.name for x in node.names if x.name != "*"]
                if prefix.startswith("base.") and resolve(prefix, owner) is None:
                    rows[owner]["missing_base_modules"].append({"module": prefix, "line": node.lineno})
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and re.fullmatch(r"(?:base|cases)(?:\.[A-Za-z_]\w*)+", node.value):
                names = [node.value]
            for name in names:
                target = resolve(name, owner)
                if target:
                    targets.add(target)
                    # Python executes existing package initializers before a submodule.
                    bits = target[:-3].replace("/", ".").split(".")
                    for end in range(1, len(bits)):
                        init = modules.get(".".join(bits[:end]))
                        if init and init.endswith("/__init__.py"):
                            targets.add(init)
        rows[owner]["imports"] = sorted(targets - {owner})
        for target in targets - {owner}:
            rows[target]["referenced_by"].append(owner)
    catalog = tomllib.loads((ROOT / "cases/catalog.toml").read_text(encoding="utf-8"))
    for case in catalog["case"]:
        for entry in case.get("entrypoints", []):
            path = "cases/" + case["path"] + "/" + entry
            if path in rows:
                rows[path]["entry_registered"] = True
                rows[path]["referenced_by"].append("cases/catalog.toml")
    # Record explicit document/config references without mistaking comments for imports.
    active_targets = [p for p in rows if not historical(p) and rows[p]["category"] not in ("environment", "generated") and not p.startswith("tests/data/")]
    basename_counts = Counter(Path(p).name for p in active_targets)
    for owner, source in texts.items():
        if historical(owner) or Path(owner).suffix not in (".md", ".toml", ".sh"):
            continue
        for target in active_targets:
            name = Path(target).name
            if target != owner and (target in source or (basename_counts[name] == 1 and name in source)):
                rows[target].setdefault("documented_by", []).append(owner)
    for row in rows.values():
        row["referenced_by"] = sorted(set(row["referenced_by"]))


def duplicates(rows):
    hashes = defaultdict(list)
    for path, row in rows.items():
        if row["category"] not in ("environment", "generated", "editor", "lock") and not path.startswith("tests/data/"):
            hashes[row["sha256"]].append(path)
    groups = []
    for digest, paths in hashes.items():
        if len(paths) < 2:
            continue
        paths.sort(key=lambda p: (historical(p), p.startswith("old/"), len(p), p))
        canonical = paths[0]
        group = {"id": len(groups) + 1, "sha256": digest, "bytes_per_file": rows[canonical]["bytes"], "paths": paths}
        groups.append(group)
        for path in paths:
            rows[path]["duplicate_group"] = group["id"]
            rows[path]["same_content_as"] = canonical if path != canonical else paths[1]
            if path != canonical and rows[path]["category"] == "history" and Path(path).name != "__init__.py":
                rows[path]["category"] = "duplicate"
                rows[path]["duplicate_keep_candidate"] = canonical
    return groups


def advice(row):
    cat = row["category"]
    if cat == "generated":
        return "可清理并重建；运行中勿删除，保留仍需引用的结果"
    if cat == "environment":
        return "不纳入项目交付；停用并确认解释器配置后可重建，不逐个删环境内部文件"
    if cat == "editor":
        return "团队交付可排除；删除会丢本机偏好"
    if cat == "lock":
        return "关闭对应 Office 文档后确认锁已失效再清理"
    if cat == "duplicate":
        return "核对旧入口路径引用后保留一份；候选保留 " + row["duplicate_keep_candidate"]
    if cat == "broken":
        return "退出案例活动清单，连同配置归档；恢复前修复旧导入并验证"
    if cat == "comparison":
        return "保留方法对照；若精简主目录可迁入 experiments，并同步登记"
    if cat == "history":
        return "不随运行包交付；保留版本/数据来源追溯，未证明可删除"
    if cat == "verification":
        return "保留测试与输入基准；相同像元内容不代表同一观测时次"
    if cat in ("core", "feature"):
        return "保留；删除会缩减公开功能或破坏调用链"
    if cat == "case":
        return "仅对应传感器/区域任务需要；停止该任务后可整体归档"
    return "保留维护；模板/配置应随其调用方一起调整"


def esc(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def link(path):
    return f"[{path}](<{os.path.relpath(ROOT / path, OUT).replace(chr(92), '/')}>)"


def write_table(filename, title, selected):
    lines = ["# " + title, "", "每个现存文件一行。‘必需’指保留对应公开功能/测试，不能理解为所有任务都会调用。", "",
             "引用仅为静态证据；未发现引用不等于可删除。完整导入、文档引用、函数列表及哈希见 inventory.json。", "",
             "| 文件 | 用途/接口证据 | 判断 | 引用/问题 | 建议 |", "|---|---|---|---|---|"]
    for row in selected:
        detail = row["purpose"]
        if row.get("docstring"):
            detail += "；模块说明：" + row["docstring"].replace("\n", " ")[:160]
        if row["symbols"]:
            detail += "；定义：" + ", ".join(row["symbols"][:5]) + (" …" if len(row["symbols"]) > 5 else "")
        refs = [p for p in row["referenced_by"] if not historical(p)]
        evidence = "登记入口；" if row["entry_registered"] else ""
        if refs:
            evidence += "引用：" + "; ".join(refs[:3]) + (f" 等 {len(refs)} 个" if len(refs) > 3 else "")
        elif row.get("documented_by"):
            evidence += "文档/配置：" + "; ".join(row["documented_by"][:2])
        elif row["category"] not in ("environment", "generated", "editor", "verification"):
            evidence += "未发现当前静态导入（非删改依据）"
        if row["missing_base_modules"]:
            evidence += "；缺失导入：" + ", ".join(x["module"] for x in row["missing_base_modules"])
        if row.get("parse_error"):
            evidence += "；语法解析失败：" + row["parse_error"]
        if row.get("duplicate_group"):
            evidence += f"；字节相同组 D{row['duplicate_group']:03}"
        lines.append("| " + " | ".join([link(row["path"]), esc(detail), LABELS[row["category"]], esc(evidence or "按文件角色保留/管理"), esc(row["advice"])]) + " |")
    (OUT / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    rows, trees, texts = scan()
    references(rows, trees, texts)
    groups = duplicates(rows)
    for row in rows.values():
        row["advice"] = advice(row)
    ordered = [rows[p] for p in sorted(rows)]
    counts = Counter(r["category"] for r in ordered)
    total = sum(r["bytes"] for r in ordered)
    missing = [r for r in ordered if r["missing_base_modules"] and not historical(r["path"])]
    broken = [r for r in ordered if r["category"] == "broken" and r["missing_base_modules"]]
    deleted = subprocess.check_output(["git", "ls-files", "--deleted", "-z"], cwd=ROOT).decode().split("\0")
    migrations = []
    for path in filter(None, deleted):
        candidate = path.replace("cases/_templates/", "base/templates/") if path.startswith("cases/_templates/") else "base/" + path
        migrations.append({"old_path": path, "existing_candidate": candidate if candidate in rows else None})
    roots = ["tests/examples/msg_evo_sample.py"]
    closure = set()
    pending = roots[:]
    while pending:
        p = pending.pop()
        if p in closure or p not in rows:
            continue
        closure.add(p)
        pending.extend(rows[p]["imports"])
    payload = {"root": str(ROOT), "generated_at": datetime.now().astimezone().isoformat(),
               "scope": "All existing files except .git directories and this audit's generated reports; no symlink traversal",
               "method": "Read bytes; parse Python AST; resolve local imports and package initializers; inspect explicit catalog/doc references; compare SHA-256. No scientific script imports/execution.",
               "limits": "Dynamic sys.path/subprocess/external consumers and runtime-only access may be missed. Binary assets inventoried but not scientifically revalidated. Equal content does not imply removable paths.",
               "file_count": len(ordered), "total_bytes": total, "category_counts": dict(counts),
               "msg_example_static_import_closure": sorted(closure), "deleted_tracked_paths": migrations,
               "duplicate_groups": groups, "files": ordered}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inventory.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    buckets = defaultdict(list)
    for row in ordered:
        cat, path = row["category"], row["path"]
        bucket = ("local" if cat in ("generated", "environment", "editor", "lock") else
                  "test_data" if path.startswith("tests/data/") else
                  "historical" if historical(path) else "active")
        buckets[bucket].append(row)
    for bucket, title in (("active", "当前源码、案例、测试和文档逐文件说明"), ("historical", "历史归档和失效快照逐文件说明"), ("test_data", "真实测试输入逐文件说明"), ("local", "本地环境、缓存和可再生输出逐文件说明")):
        write_table(bucket + "_files.md", title, buckets[bucket])
    dlines = ["# 内容完全相同的文件组", "", "仅比较源码/文档/历史资产；不把缓存、环境、IDE 设置或真实多时次测试输入纳入重复候选。", "",
              "SHA-256 相同只证明内容相同。模板、包入口和被路径引用的文件仍可能必须分别存在，不能直接删组内副本。", ""]
    for group in groups:
        dlines += [f"## D{group['id']:03} · {len(group['paths'])} 份 · 每份 {group['bytes_per_file']} 字节", "", f"SHA-256: `{group['sha256']}`", ""]
        dlines += [f"- {link(p)} — {LABELS[rows[p]['category']]}" for p in group["paths"]]
        dlines.append("")
    (OUT / "duplicates.md").write_text("\n".join(dlines), encoding="utf-8")
    validation_path = OUT / "validation.txt"
    validation = validation_path.read_text(encoding="utf-8-sig", errors="replace") if validation_path.exists() else "本次未运行 pytest。"
    # PowerShell redirection can produce UTF-16 in older hosts.
    if "\x00" in validation:
        validation = validation_path.read_text(encoding="utf-16")
    (OUT / "validation.txt").write_text(validation, encoding="utf-8")
    pytest_summary = next((s for s in validation.splitlines() if re.search(r"\d+ (failed|passed).* in ", s)), "见 validation.txt；无可解析测试汇总")
    validation_time = datetime.fromtimestamp(validation_path.stat().st_mtime).astimezone().isoformat() if validation_path.exists() else "未记录"
    parse_errors = [r for r in ordered if r.get("parse_error")]
    lines = ["# LS4T 逐文件用途与必要性审阅", "", f"审阅目录：`{ROOT}`。生成时间：{payload['generated_at']}。", "",
             f"共登记 **{len(ordered)} 个现存文件，{total / 2**20:.2f} MiB**。每个文件均有用途、判断、建议、字节数和 SHA-256；清单生成器不修改科学代码。", "",
             "排除 Git 内部数据库及本报告生成文件自身；包含隐藏目录、历史源码、真实样例、虚拟环境及缓存。历史压缩包/文档/图片按文件登记，未解包或逐页验证内容。", "",
             "## 判断结论", "",
             "保留 `base/` 的公共 API 和传感器功能、当前案例配置/入口、自动化测试以及 EVO 真实输入。优先清理可再生缓存/输出；历史相同副本可在核对路径依赖后精简。旧科学实现和实验变体应归档，不应直接删除。", "",
             "| 类别 | 文件数 | 大小 MiB | 判断依据 |", "|---|---:|---:|---|"]
    for cat, count in sorted(counts.items()):
        size = sum(r["bytes"] for r in ordered if r["category"] == cat) / 2**20
        lines.append(f"| {LABELS[cat]} | {count} | {size:.2f} | {esc(advice({'category': cat, 'duplicate_keep_candidate': '逐文件清单列出的候选路径'}))} |")
    lines += ["", "## 完整逐文件清单", "",
              f"- [当前源码、案例、测试和说明](file_audit/active_files.md)：{len(buckets['active'])} 个。",
              f"- [历史归档与失效快照](file_audit/historical_files.md)：{len(buckets['historical'])} 个。",
              f"- [真实测试输入](file_audit/test_data_files.md)：{len(buckets['test_data'])} 个，每个时次单列。",
              f"- [环境、缓存与生成输出](file_audit/local_files.md)：{len(buckets['local'])} 个。",
              f"- [完全相同的副本组](file_audit/duplicates.md)：{len(groups)} 组，组内超出第一份的文件共 {sum(len(g['paths']) - 1 for g in groups)} 个；这不是可直接删除的文件数。",
              "- [机器可读清单](file_audit/inventory.json)：全量符号、导入、引用、哈希、迁移路径和 MSG 示例静态依赖闭包。", "",
              "## 优先处理的具体问题", "",
              "1. **失效入口已归档。** 两组 SLSTR 旧区域目录现位于 `cases/_archive/slstr/retired_20261013/`，其 case.toml 标记 archived，并已移出 catalog 的 case 登记。",
              "2. **相同历史副本已精简。** 247 个副本移至项目外可恢复目录。保留路径和 SHA-256 见 `cases/_archive/DEDUPLICATED_FILES.json`；精确恢复历史目录使用清理前 ZIP。",
              "3. **五个 MSG 对照脚本已改名并集中。** 当前位于 `cases/msg/experiments/`，按 window、two_stage、constrained、diagnostics 命名；正式入口仍是 `msg_lsct_iter.py`，数值实现未变。",
              "4. **本地旧环境和可再生文件已移出。** 未使用的 `.venv` 与本轮列出的缓存/输出保存到外部 quarantine；外部 Conda python311 环境保留。`.gitignore` 已排除本地环境和 IDE 设置。",
              "5. **依赖与文档已同步。** h5py、scipy、scikit-learn 作为 base 传递导入的基础依赖列入 pyproject；样例、案例状态和对照路径说明已修正。",
              "6. **保留必要的相似实现。** 案例模板执行器依赖各自目录；历史 Planck/窗口接口仍有调用；未证明被替代的研究备忘录、备份包和 MSG 角度生成脚本继续保留。",
              "处理详情、备份位置和改名前后对应关系见 [清理记录](CLEANUP_20261013.md)。本报告的清理结论对应 2026-10-13 这一轮，未来审阅需重新核对现场。", "",
              "## 什么是必须保留", "",
              "- **完整项目维护：** base 公开功能、项目元数据、相应案例配置、测试及数据基准应保留；不因未被本仓库导入就删除公开函数。",
              "- **仅运行当前 MSG EVO 示例：** 保留 tests/examples/msg_evo_sample.py、完整 tests/data/msg_evo_201710_10x10、其 base 导入链及科学计算环境。全体历史案例和其他传感器案例不参与该示例。",
              f"- 该示例的静态 Python 导入闭包共有 {len(closure)} 个文件（见 JSON）；包含包初始化、条件分支及兼容导入，因此是保守集合，不是经过删文件实验验证的最小发行包。",
              "- 样例的 1,519 个产品 TIFF 具有独立时次身份，即使某些全缺测栅格内容相同也必须保留；4 个 Static、3 个 AUXILIARY 与 2 个来源/格式 JSON 同样服务离线测试。", "",
              "## 验证及边界", "",
              f"- Conda python311 完整测试结果：**{pytest_summary}**，日志更新时间 {validation_time}，输出见 [validation.txt](file_audit/validation.txt)。",
              "- 本轮已改写误触结构检查的历史注释。仍有既有的窗口反演 golden 差异约 0.0042 K，未修改科学算法、预期值或放宽容差；详见本轮测试日志。",
              "- `base/templates/audit_cases.py` 清理后实跑通过 5 个登记案例。它只检查结构，不能替代真实数据验证。",
              f"- 当前非历史 Python 文件静态扫描发现 {len(missing)} 个文件存在缺失 base 模块导入。动态 sys.path、外部调用和 subprocess 参数仍可能遗漏。",
              f"- 成功解析 {len(trees)} 个项目 Python 文件；另有 {len(parse_errors)} 个历史文件存在语法错误，逐文件清单列出了错误位置。这些文件不能直接恢复为运行入口。",
              f"- Git 中另有 {len(migrations)} 个已跟踪但工作区不存在的旧路径；候选新位置列于 JSON。它们不是当前可再删的物理副本，重组尚需独立提交/审阅。",
              "- 历史脚本只解析，不批量 import/执行，避免硬编码路径触发下载、数据写入或生产计算。未导入、语法失败、同名均不直接等于冗余。", "",
              "重新生成：`python -B docs/file_audit/generate_inventory.py`。测试日志使用 docs/file_audit/validation.txt；测试与案例审计需单独重跑。", ""]
    (ROOT / "docs/FILE_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"file_count": len(ordered), "buckets": {k: len(v) for k, v in buckets.items()}, "categories": dict(counts), "duplicate_groups": len(groups), "broken_import_files": len(broken), "msg_import_closure": len(closure)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
