"""Tests for the expert_functional task.

This task requires a CORRECT merge of both branches:
  - refactor-safety: ZeroDivisionError guard in divide(), type hints, safety demo
  - feature-advanced: import math, power(), sqrt(), absolute(), advanced demo

Critically, some tests are IMPOSSIBLE to pass unless both branches are merged:
  - test_divide_raises_zero_division  → requires refactor-safety's guard
  - test_power_functional             → requires feature-advanced's method
  - test_sqrt_raises_on_negative      → requires feature-advanced's ValueError guard
"""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest


def _load_module(workspace_path: str, name: str):
    """Dynamically load a Python module from the workspace directory."""
    path = Path(workspace_path) / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ── Structural: no conflict markers ───────────────────────────────────────────

def test_no_conflict_markers_calculator(workspace_path):
    content = (Path(workspace_path) / "calculator.py").read_text(encoding="utf-8")
    assert "<<<<<<< " not in content, "Conflict start marker in calculator.py"
    assert ">>>>>>> " not in content, "Conflict end marker in calculator.py"
    for line in content.splitlines():
        assert line.strip() != "=" * 7, "Conflict separator in calculator.py"


def test_no_conflict_markers_main(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    assert "<<<<<<< " not in content, "Conflict start marker in main.py"
    assert ">>>>>>> " not in content, "Conflict end marker in main.py"
    for line in content.splitlines():
        assert line.strip() != "=" * 7, "Conflict separator in main.py"


# ── Structural: valid Python ───────────────────────────────────────────────────

def test_calculator_valid_python(workspace_path):
    content = (Path(workspace_path) / "calculator.py").read_text(encoding="utf-8")
    ast.parse(content)


def test_main_valid_python(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    ast.parse(content)


# ── Structural: both branches present ─────────────────────────────────────────

def test_has_math_import(workspace_path):
    content = (Path(workspace_path) / "calculator.py").read_text(encoding="utf-8")
    assert "import math" in content, "Missing 'import math' from feature-advanced branch"


def test_has_power_method(workspace_path):
    content = (Path(workspace_path) / "calculator.py").read_text(encoding="utf-8")
    assert "def power" in content, "Missing power() from feature-advanced branch"


def test_has_sqrt_method(workspace_path):
    content = (Path(workspace_path) / "calculator.py").read_text(encoding="utf-8")
    assert "def sqrt" in content, "Missing sqrt() from feature-advanced branch"


def test_has_absolute_method(workspace_path):
    content = (Path(workspace_path) / "calculator.py").read_text(encoding="utf-8")
    assert "def absolute" in content, "Missing absolute() from feature-advanced branch"


def test_has_zero_division_guard(workspace_path):
    content = (Path(workspace_path) / "calculator.py").read_text(encoding="utf-8")
    assert "ZeroDivisionError" in content, \
        "Missing ZeroDivisionError guard from refactor-safety branch"


def test_main_has_advanced_demo(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    assert "def run_advanced_demo" in content, \
        "Missing run_advanced_demo() from feature-advanced branch"


def test_main_has_safety_demo(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    assert "ZeroDivisionError" in content or "except" in content, \
        "Missing safety try/except from refactor-safety branch"


# ── Functional: basic operations ───────────────────────────────────────────────

def test_add_functional(workspace_path):
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    assert calc.add(2, 3) == 5
    assert calc.add(-1, 1) == 0
    assert calc.add(0.5, 0.5) == pytest.approx(1.0)


def test_subtract_functional(workspace_path):
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    assert calc.subtract(10, 4) == 6
    assert calc.subtract(0, 5) == -5


def test_multiply_functional(workspace_path):
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    assert calc.multiply(3, 7) == 21
    assert calc.multiply(-2, 5) == -10


def test_divide_functional(workspace_path):
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    assert calc.divide(15, 3) == pytest.approx(5.0)
    assert calc.divide(1, 4) == pytest.approx(0.25)


# ── Functional: refactor-safety branch (ZeroDivisionError) ────────────────────

def test_divide_raises_zero_division(workspace_path):
    """This test ONLY passes if refactor-safety's guard is correctly merged."""
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    with pytest.raises(ZeroDivisionError):
        calc.divide(10, 0)


# ── Functional: feature-advanced branch (power, sqrt, absolute) ────────────────

def test_power_functional(workspace_path):
    """This test ONLY passes if feature-advanced's power() is correctly merged."""
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    assert calc.power(2, 10) == pytest.approx(1024.0)
    assert calc.power(3, 3) == pytest.approx(27.0)
    assert calc.power(5, 0) == pytest.approx(1.0)


def test_sqrt_functional(workspace_path):
    """This test ONLY passes if feature-advanced's sqrt() is correctly merged."""
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    assert calc.sqrt(16) == pytest.approx(4.0)
    assert calc.sqrt(2) == pytest.approx(1.4142135, rel=1e-5)
    assert calc.sqrt(0) == pytest.approx(0.0)


def test_sqrt_raises_on_negative(workspace_path):
    """This test ONLY passes if feature-advanced's sqrt() guard is present."""
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    with pytest.raises(ValueError):
        calc.sqrt(-1)


def test_absolute_functional(workspace_path):
    calc_mod = _load_module(workspace_path, "calculator")
    calc = calc_mod.Calculator()
    assert calc.absolute(-5) == 5
    assert calc.absolute(5) == 5
    assert calc.absolute(0) == 0
