"""Build the LS4T Windows installer from an explicit source/runtime snapshot."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files(root: Path) -> list[Path]:
    files = [root / "README.md", root / "pyproject.toml"]
    for folder in ("base", "gui", "docs", "tests", "scripts"):
        for path in (root / folder).rglob("*"):
            parts = path.relative_to(root).parts
            if not path.is_file() or any(x in parts for x in ("__pycache__", ".pytest_cache", "outputs", "superpowers", "file_audit")):
                continue
            if path.suffix in (".pyc", ".log") or path.name in ("tasks.json", "local.json", "CLEANUP_20261013.json"):
                continue
            files.append(path)
    case = root / "cases/ahi-slstr/heihe/three-site-kernel-3x3"
    files += [p for p in case.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    files.append(root / "cases/README.md")
    return sorted(set(files))


def copy_runtime(source: Path, target: Path, report: dict) -> None:
    target.mkdir()
    skip_packages = {"cv2", "playwright", "selenium", "pip", "PyInstaller", "_pyinstaller_hooks_contrib", "__pycache__", "PyQt6", "PySide6", "shiboken6", "pyarrow", "pyarrow.libs", "numba", "llvmlite", "conda", "conda_env", "libmambapy", "tests"}
    skip_distributions = ("opencv", "playwright", "selenium", "pip-", "pyinstaller", "pyinstaller_hooks")
    def ignored(folder, names):
        dropped = []
        for name in names:
            if name == "__pycache__" or name.endswith((".pyc", ".pdb")):
                dropped.append(name)
            elif Path(folder) == source / "Lib/site-packages" and (name in skip_packages or name.lower().startswith(skip_distributions) or any(name.lower().startswith(x.lower() + "-") for x in skip_packages) or name.endswith(".pth")):
                dropped.append(name)
        return dropped
    for path in source.iterdir():
        if path.is_file() and (path.suffix.lower() in (".exe", ".dll") or path.name.startswith("LICENSE")):
            shutil.copy2(path, target / path.name)
    for name in ("Lib", "DLLs"):
        shutil.copytree(source / name, target / name, ignore=ignored)
    binary = target / "Library/bin"
    binary.mkdir(parents=True)
    for path in (source / "Library/bin").iterdir():
        if path.is_file() and path.suffix.lower() == ".dll":
            shutil.copy2(path, binary / path.name)
    for name in ("Library/share/gdal", "Library/share/proj", "Library/share/doc", "Library/lib/gdalplugins", "conda-meta"):
        if (source / name).is_dir():
            shutil.copytree(source / name, target / name, ignore=ignored)
    report["runtime_source"] = str(source)
    report["excluded_optional_tools"] = sorted(skip_packages - {"__pycache__"})


def build(args) -> None:
    root = Path(__file__).resolve().parents[1]
    stage = args.staging.resolve()
    if stage.exists():
        raise SystemExit("Existing staging directory retained: " + str(stage))
    version = re.search(r'^version\s*=\s*"([^"]+)"', (root / "pyproject.toml").read_text(), re.M).group(1)
    output = args.output_root.resolve()
    setup_name = f"LS4T-Setup-{version}-x64.exe"
    if (output / setup_name).exists():
        raise SystemExit("Existing release retained: " + str(output / setup_name))
    stage.mkdir(parents=True)
    status = {"version": version, "started_at": datetime.datetime.now().isoformat(), "status": "running"}
    def record(step):
        status["stage"] = step
        (stage / "BUILD_STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(step, flush=True)
    env = os.environ.copy()
    env["PATH"] = str(args.python_env) + ";" + str(args.python_env / "Library/bin") + ";" + env.get("PATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        record("Snapshotting source")
        files = source_files(root)
        before = {p.relative_to(root).as_posix(): sha(p) for p in files}
        payload = stage / "payload"
        app = payload / "app"
        app.mkdir(parents=True)
        for path in files:
            dest = app / path.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        (payload / "SOURCE_MANIFEST.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
        record("Copying independent Python and geospatial runtime")
        copy_runtime(args.python_env.resolve(), payload / "runtime", status)
        shutil.copy2(root / "scripts/runtime_sitecustomize.py", payload / "runtime/Lib/sitecustomize.py")
        record("Checking relocated scientific modules")
        check_env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "GDAL_DATA", "PROJ_LIB", "PROJ_DATA")}
        check_env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
        check_env["PYTHONNOUSERSITE"] = "1"
        probe = "import sys,json,numpy,scipy.linalg,sklearn,h5py,pandas,netCDF4,matplotlib,rasterio;from osgeo import gdal,osr;s=osr.SpatialReference();s.ImportFromEPSG(4326);print(json.dumps({'python':sys.executable,'prefix':sys.prefix,'numpy':numpy.__version__,'gdal':gdal.VersionInfo(),'projection':s.GetAuthorityCode(None),'solve':scipy.linalg.solve([[2.,0.],[0.,3.]],[4.,9.]).tolist(),'origins':{m.__name__:m.__file__ for m in [numpy,sklearn,h5py,pandas,netCDF4,matplotlib,rasterio]}}))"
        q = subprocess.run([str(payload / "runtime/python.exe"), "-I", "-B", "-c", probe], cwd=str(stage), env=check_env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=150)
        status["runtime_check"] = {"exit": q.returncode, "stdout": q.stdout, "stderr": q.stderr}
        if q.returncode:
            raise RuntimeError("Relocated runtime failed: " + q.stderr[-2500:])
        if str(args.python_env).lower() in q.stdout.lower():
            raise RuntimeError("Relocated module check points to source environment")
        record("Verifying frozen real-data case with bundled runtime")
        case = app / "cases/ahi-slstr/heihe/three-site-kernel-3x3"
        command = [str(payload / "runtime/python.exe"), "-B", str(case / "run.py"), "--replay", str(case / "data/2019-05-12-s3b"), "--output-parent", str(stage / "reference-case-replay")]
        q = subprocess.run(command, cwd=str(case), env=check_env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        status["reference_case_replay"] = {"exit": q.returncode, "stdout": q.stdout, "stderr": q.stderr}
        if q.returncode:
            raise RuntimeError("Frozen case replay failed: " + q.stderr[-2000:])
        record("Building LS4T launcher executable")
        command = [str(args.python_env / "python.exe"), "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console", "--name", "LS4T", "--distpath", str(payload), "--workpath", str(stage / "launcher-work"), "--specpath", str(stage), str(root / "scripts/launcher.py")]
        subprocess.run(command, cwd=str(root), env=env, check=True, timeout=300)
        record("Recording bundled package versions")
        q = subprocess.run([str(payload / "runtime/python.exe"), "-I", "-c", "import importlib.metadata as m,json;print(json.dumps({p.metadata['Name']:p.version for p in m.distributions()},sort_keys=True))"], cwd=str(stage), env=check_env, capture_output=True, text=True, encoding="utf-8", check=True, timeout=45)
        (payload / "RUNTIME_PACKAGES.json").write_text(q.stdout, encoding="utf-8")
        (payload / "README.txt").write_text("LS4T " + version + "\n\nRun LS4T.exe to open the local browser workbench. Close its console to stop it.\nUser settings: %LOCALAPPDATA%\\LS4T. Source and method documents: app\\docs.\nLarge satellite data are not bundled. Satpy and pyepr are optional and not bundled.\nThird-party notices are included in runtime package metadata and Library/share/doc.\n", encoding="utf-8")
        manifest = {p.relative_to(payload).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in payload.rglob("*") if p.is_file()}
        (payload / "PAYLOAD_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        status["payload_files"] = len(manifest)
        status["payload_bytes"] = sum(x["bytes"] for x in manifest.values())
        record("Compiling current-user NSIS installer")
        nsi = '''Unicode true
!include "MUI2.nsh"
!include "FileFunc.nsh"
Name "LS4T VERSION"
OutFile "SETUP"
InstallDir "$LOCALAPPDATA\\Programs\\LS4T"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
ShowInstDetails show
ShowUninstDetails show
Var TestMode
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
Function .onInit
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/TESTMODE" $R1
  IfErrors normal_init
  StrCpy $TestMode "1"
normal_init:
FunctionEnd
Section "LS4T"
  SetOutPath "$INSTDIR"
  File /r "PAYLOAD\\*"
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  StrCmp $TestMode "1" test_install
  CreateDirectory "$SMPROGRAMS\\LS4T"
  CreateShortcut "$SMPROGRAMS\\LS4T\\LS4T.lnk" "$INSTDIR\\LS4T.exe"
  CreateShortcut "$SMPROGRAMS\\LS4T\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LS4T" "DisplayName" "LS4T VERSION"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LS4T" "DisplayVersion" "VERSION"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LS4T" "UninstallString" '"$INSTDIR\\Uninstall.exe"'
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LS4T" "InstallLocation" "$INSTDIR"
  Goto installed
test_install:
  FileOpen $R0 "$INSTDIR\\test-install.flag" w
  FileWrite $R0 "isolated installation verification"
  FileClose $R0
installed:
SectionEnd
Section "Uninstall"
  IfFileExists "$INSTDIR\\test-install.flag" skip_registration
  Delete "$SMPROGRAMS\\LS4T\\LS4T.lnk"
  Delete "$SMPROGRAMS\\LS4T\\Uninstall.lnk"
  RMDir "$SMPROGRAMS\\LS4T"
  DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LS4T"
skip_registration:
  RMDir /r "$INSTDIR\\app"
  RMDir /r "$INSTDIR\\runtime"
  Delete "$INSTDIR\\LS4T.exe"
  Delete "$INSTDIR\\SOURCE_MANIFEST.json"
  Delete "$INSTDIR\\PAYLOAD_MANIFEST.json"
  Delete "$INSTDIR\\RUNTIME_PACKAGES.json"
  Delete "$INSTDIR\\README.txt"
  Delete "$INSTDIR\\test-install.flag"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir "$INSTDIR"
SectionEnd
'''
        nsi = nsi.replace("VERSION", version).replace("SETUP", str(stage / setup_name)).replace('"PAYLOAD\\*"', '"' + str(payload) + '\\*"')
        script = stage / "installer.nsi"
        script.write_text(nsi, encoding="utf-8-sig")
        subprocess.run([str(args.makensis), "/V2", str(script)], cwd=str(stage), check=True, timeout=1200)
        after = {p.relative_to(root).as_posix(): sha(p) for p in source_files(root)}
        if before != after:
            raise RuntimeError("Source changed during build; release was not promoted")
        record("Writing source archive and checksums")
        output.mkdir(parents=True, exist_ok=True)
        archive = stage / f"LS4T-{version}-source.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for path in files:
                z.write(path, "LS4T-" + version + "/" + path.relative_to(root).as_posix())
        with zipfile.ZipFile(archive) as z:
            if z.testzip():
                raise RuntimeError("Source ZIP CRC check failed")
        artifacts = [stage / setup_name, archive, payload / "SOURCE_MANIFEST.json", payload / "RUNTIME_PACKAGES.json", payload / "PAYLOAD_MANIFEST.json"]
        for path in artifacts:
            dest = output / path.name
            if dest.exists() and sha(dest) != sha(path):
                raise RuntimeError("Different existing release retained: " + str(dest))
            if not dest.exists():
                shutil.copy2(path, dest)
            if sha(path) != sha(dest):
                raise RuntimeError("Release copy mismatch")
        (output / "SHA256SUMS.txt").write_text("\n".join(sha(p) + "  " + p.name for p in artifacts) + "\n", encoding="utf-8")
        status.update(status="completed", installer=str(output / setup_name), installer_sha256=sha(output / setup_name), finished_at=datetime.datetime.now().isoformat())
        record("Build completed")
        (output / "BUILD_RECEIPT.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as error:
        status.update(status="failed", error=str(error))
        record("Build failed")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-env", type=Path, required=True)
    parser.add_argument("--makensis", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    build(parser.parse_args())
