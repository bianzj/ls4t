"""Reference cases must remain executable without the LS4T checkout."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import runpy
import subprocess
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("components", "normalization", "kernel_atc")


@pytest.fixture(autouse=True)
def external_storage(tmp_path, monkeypatch):
    storage = tmp_path.parent / (tmp_path.name + "-storage")
    monkeypatch.setenv("LS4T_DATA_ROOT", str(storage / "data"))
    monkeypatch.setenv("LS4T_PRODUCT_ROOT", str(storage / "products"))


@pytest.mark.parametrize("name", NAMES)
def test_reference_runs_outside_checkout(name, tmp_path):
    source = ROOT / "base" / "templates" / "references" / name
    target = tmp_path / name
    shutil.copytree(source, target)
    script = target / "run.py"
    for node in ast.walk(ast.parse(script.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert not (node.module or "").startswith(("base", "cases"))
        if isinstance(node, ast.Import):
            assert all(not x.name.startswith(("base", "cases")) for x in node.names)
    result = subprocess.run([sys.executable, "-I", str(script)], cwd=tmp_path,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    output = Path(os.environ["LS4T_PRODUCT_ROOT"]) / name / "demo.npz"
    assert not (target / "outputs").exists()
    with np.load(output, allow_pickle=False) as data:
        if name == "components":
            np.testing.assert_allclose(data["temperature_k"], [300., 310.], atol=1e-8)
        elif name == "normalization":
            fine = data["temperature_k"]
            np.testing.assert_allclose(fine.reshape(3, 2, 4, 2).mean((1, 3)),
                                       data["normalized_coarse_k"], atol=1e-10)
            assert np.isfinite(fine).all()
        else:
            np.testing.assert_allclose(data["kernel_coefficients"], [300., 2., 3.], atol=1e-7)
            np.testing.assert_allclose(data["atc_coefficients"], [290., -8., 4., 2., 1.], atol=1e-8)
    before = output.read_bytes()
    again = subprocess.run([sys.executable, "-I", str(script)], cwd=tmp_path,
                           capture_output=True, text=True)
    assert again.returncode != 0
    assert output.read_bytes() == before
    manifest = json.loads((target / "SOURCE_SNAPSHOT.json").read_text(encoding="utf-8"))
    assert manifest["sources"]
    assert manifest["reference_sha256"] == hashlib.sha256(script.read_bytes()).hexdigest()


@pytest.mark.parametrize("name", NAMES)
def test_prepared_npz_batch(name, tmp_path):
    script = tmp_path / "run.py"
    shutil.copy2(ROOT / "base" / "templates" / "references" / name / "run.py", script)
    namespace = runpy.run_path(str(script))
    data = namespace["demo_input"]()
    if name == "normalization":
        data["coarse_quality_flag"][0, 0] = 2  # Cloud: parent must stay missing.
    data_dir = Path(os.environ["LS4T_DATA_ROOT"]) / tmp_path.name
    data_dir.mkdir(parents=True)
    np.savez(data_dir / "scene.npz", **data)
    text = script.read_text(encoding="utf-8").replace("USE_DEMO = True", "USE_DEMO = False")
    text = text.replace("INPUT_FILES = []", 'INPUT_FILES = ["scene.npz"]')
    script.write_text(text, encoding="utf-8")
    result = subprocess.run([sys.executable, "-I", str(script)], cwd=tmp_path.parent,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with np.load(Path(os.environ["LS4T_PRODUCT_ROOT"]) / tmp_path.name / "scene.npz") as output:
        assert not output["synthetic_demo"]
        assert output["input_source"].item() == str((data_dir / "scene.npz").resolve())
        if name == "normalization":
            assert np.isnan(output["temperature_k"][:2, :2]).all()
            assert ((output["quality_flag"][:2, :2] & 2) != 0).all()


@pytest.mark.parametrize("sensor", ["slstr", "slstr-modis"])
def test_new_case_default_is_standalone(tmp_path, sensor):
    # Run the generator in a throwaway checkout, never create a production case.
    templates = tmp_path / "base" / "templates"
    templates.mkdir(parents=True)
    shutil.copy2(ROOT / "base" / "templates" / "new_case.py", templates)
    shutil.copytree(ROOT / "base" / "templates" / "references", templates / "references")
    command = [sys.executable, str(templates / "new_case.py"), sensor, "heihe", "test-copy"]
    created = subprocess.run(command, capture_output=True, text=True)
    assert created.returncode == 0, created.stdout + created.stderr
    case = tmp_path / "cases" / sensor / "heihe" / "test-copy"
    assert (case / "run.py").exists()
    manifest = json.loads((case / "SOURCE_SNAPSHOT.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((case / "run.py").read_bytes()).hexdigest() == manifest["reference_sha256"]
    assert not (case / "run_standard_stage.py").exists()
    result = subprocess.run([sys.executable, "-I", str(case / "run.py")],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert subprocess.run(command, capture_output=True).returncode != 0
    invalid = subprocess.run(command[:2] + ["../outside", "heihe", "invalid"], capture_output=True)
    assert invalid.returncode != 0


def test_legacy_template_remains_explicit(tmp_path):
    templates = tmp_path / "base" / "templates"
    shutil.copytree(ROOT / "base" / "templates", templates)
    result = subprocess.run([sys.executable, str(templates / "new_case.py"),
                             "slstr", "heihe", "legacy", "--legacy-template", "--mode", "scene-first"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    target = tmp_path / "cases" / "slstr" / "heihe" / "legacy"
    assert (target / "run_standard_stage.py").exists()
    config = (target / "case.toml").read_text(encoding="utf-8")
    assert "{{" not in config
    assert "scene-first" in config


@pytest.mark.parametrize("name", NAMES)
def test_reference_rejects_output_in_code(name, tmp_path, monkeypatch):
    script = tmp_path / "run.py"
    shutil.copy2(ROOT / "base/templates/references" / name / "run.py", script)
    monkeypatch.setenv("LS4T_PRODUCT_ROOT", str(tmp_path / "forbidden-products"))
    result = subprocess.run([sys.executable, "-I", str(script)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "outside" in result.stderr
    assert not (tmp_path / "forbidden-products").exists()


def test_active_code_tree_contains_no_product_directories():
    for folder in (ROOT / "base", ROOT / "cases"):
        bad = [p for p in folder.rglob("*") if p.is_dir()
               and p.name.lower() in {"outputs", "output", "products", "results"}
               and "_archive" not in p.parts]
        assert not bad, bad


@pytest.mark.parametrize("name", NAMES)
def test_reference_requires_explicit_storage(name, tmp_path, monkeypatch):
    monkeypatch.delenv("LS4T_DATA_ROOT", raising=False)
    monkeypatch.delenv("LS4T_PRODUCT_ROOT", raising=False)
    script = tmp_path / "run.py"
    shutil.copy2(ROOT / "base/templates/references" / name / "run.py", script)
    result = subprocess.run([sys.executable, "-I", str(script)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Set LS4T_DATA_ROOT and LS4T_PRODUCT_ROOT" in result.stderr
    assert list(tmp_path.iterdir()) == [script]
