"""Tests for the medium_import_conflict task.

The correct resolution must merge BOTH feature branches:
  - feature-logging: adds import logging, _log, logging calls in process()
  - feature-validation: adds import re, _WORD_RE, validate() method, filter_valid()

Structural tests verify both branches are present.
Functional tests verify the code actually executes correctly.
"""

import ast
import importlib.util
import sys
from pathlib import Path


def _load_module(workspace_path: str, name: str):
    """Dynamically load a Python module from the workspace directory."""
    path = Path(workspace_path) / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ── Structural: no conflict markers ───────────────────────────────────────────

def test_no_conflict_markers_processor(workspace_path):
    content = (Path(workspace_path) / "processor.py").read_text(encoding="utf-8")
    assert "<<<<<<< " not in content, "Conflict start marker found in processor.py"
    assert ">>>>>>> " not in content, "Conflict end marker found in processor.py"
    for line in content.splitlines():
        assert line.strip() != "=" * 7, "Conflict separator found in processor.py"


def test_no_conflict_markers_pipeline(workspace_path):
    content = (Path(workspace_path) / "pipeline.py").read_text(encoding="utf-8")
    assert "<<<<<<< " not in content, "Conflict start marker found in pipeline.py"
    assert ">>>>>>> " not in content, "Conflict end marker found in pipeline.py"
    for line in content.splitlines():
        assert line.strip() != "=" * 7, "Conflict separator found in pipeline.py"


# ── Structural: valid Python ───────────────────────────────────────────────────

def test_processor_valid_python(workspace_path):
    content = (Path(workspace_path) / "processor.py").read_text(encoding="utf-8")
    ast.parse(content)


def test_pipeline_valid_python(workspace_path):
    content = (Path(workspace_path) / "pipeline.py").read_text(encoding="utf-8")
    ast.parse(content)


# ── Structural: both branches present ─────────────────────────────────────────

def test_has_logging_import(workspace_path):
    content = (Path(workspace_path) / "processor.py").read_text(encoding="utf-8")
    assert "import logging" in content, "Missing 'import logging' from feature-logging branch"


def test_has_re_import(workspace_path):
    content = (Path(workspace_path) / "processor.py").read_text(encoding="utf-8")
    assert "import re" in content, "Missing 'import re' from feature-validation branch"


def test_has_validate_method(workspace_path):
    content = (Path(workspace_path) / "processor.py").read_text(encoding="utf-8")
    assert "def validate" in content, "Missing validate() method from feature-validation branch"


def test_has_log_calls(workspace_path):
    content = (Path(workspace_path) / "processor.py").read_text(encoding="utf-8")
    assert "_log" in content or "logging" in content, \
        "Missing logging calls from feature-logging branch"


def test_pipeline_has_logging_import(workspace_path):
    content = (Path(workspace_path) / "pipeline.py").read_text(encoding="utf-8")
    assert "import logging" in content, "Missing logging import in pipeline.py from feature-logging"


def test_pipeline_has_filter_valid(workspace_path):
    content = (Path(workspace_path) / "pipeline.py").read_text(encoding="utf-8")
    assert "def filter_valid" in content, "Missing filter_valid() from feature-validation branch"


# ── Functional: processor.validate() ──────────────────────────────────────────

def test_validate_accepts_normal_text(workspace_path):
    mod = _load_module(workspace_path, "processor")
    dp = mod.DataProcessor()
    assert dp.validate("hello") is True
    assert dp.validate("  world  ") is True
    assert dp.validate("Python 3") is True


def test_validate_rejects_empty_and_whitespace(workspace_path):
    mod = _load_module(workspace_path, "processor")
    dp = mod.DataProcessor()
    assert dp.validate("") is False
    assert dp.validate("   ") is False
    assert dp.validate("\t\n") is False


# ── Functional: processor.process() ───────────────────────────────────────────

def test_process_strips_and_lowercases(workspace_path):
    mod = _load_module(workspace_path, "processor")
    dp = mod.DataProcessor()
    assert dp.process("  Hello World  ") == "hello world"
    assert dp.process("Python") == "python"
    assert dp.process("  UPPER  ") == "upper"


def test_process_raises_on_invalid_input(workspace_path):
    """Validates that feature-validation's guard is present in process()."""
    import pytest
    mod = _load_module(workspace_path, "processor")
    dp = mod.DataProcessor()
    with pytest.raises((ValueError, Exception)):
        dp.process("")
    with pytest.raises((ValueError, Exception)):
        dp.process("   ")


# ── Functional: pipeline.filter_valid() ───────────────────────────────────────

def test_filter_valid_functional(workspace_path):
    _load_module(workspace_path, "processor")  # load first so pipeline import resolves
    pipe = _load_module(workspace_path, "pipeline")
    result = pipe.filter_valid(["hello", "", "  ", "world", "42"])
    assert "hello" in result, "filter_valid should keep 'hello'"
    assert "world" in result, "filter_valid should keep 'world'"
    assert "" not in result, "filter_valid should drop empty string"
    assert "  " not in result, "filter_valid should drop whitespace-only string"


def test_run_pipeline_functional(workspace_path):
    _load_module(workspace_path, "processor")
    pipe = _load_module(workspace_path, "pipeline")
    result = pipe.run_pipeline(["  Hello  ", "World", "Python"])
    assert "hello" in result
    assert "world" in result
    assert "python" in result
