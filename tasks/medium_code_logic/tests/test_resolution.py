"""Tests for the medium task: code function conflict resolution."""

import ast
import importlib.util
import sys
from pathlib import Path


def _load_module(workspace_path, module_name):
    """Dynamically load a module from the workspace."""
    module_path = Path(workspace_path) / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_no_conflict_markers_utils(workspace_path):
    content = (Path(workspace_path) / "utils.py").read_text(encoding="utf-8")
    assert "<<<<<<< " not in content, "Conflict marker in utils.py"
    assert ">>>>>>> " not in content, "Conflict marker in utils.py"


def test_no_conflict_markers_main(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    assert "<<<<<<< " not in content, "Conflict marker in main.py"
    assert ">>>>>>> " not in content, "Conflict marker in main.py"


def test_utils_valid_python(workspace_path):
    content = (Path(workspace_path) / "utils.py").read_text(encoding="utf-8")
    ast.parse(content)


def test_main_valid_python(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    ast.parse(content)


def test_process_items_has_type_hints(workspace_path):
    content = (Path(workspace_path) / "utils.py").read_text(encoding="utf-8")
    assert "List[str]" in content or "list[str]" in content, "Missing type hints from refactor branch"


def test_search_items_exists(workspace_path):
    content = (Path(workspace_path) / "utils.py").read_text(encoding="utf-8")
    assert "def search_items" in content, "Missing search_items function from feature branch"


def test_run_search_exists(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    assert "def run_search" in content, "Missing run_search function from feature branch"


def test_search_items_imported(workspace_path):
    content = (Path(workspace_path) / "main.py").read_text(encoding="utf-8")
    assert "search_items" in content, "search_items not imported in main.py"


def test_process_items_functional(workspace_path):
    utils = _load_module(workspace_path, "utils")
    result = utils.process_items(data=["  Hello ", "World  ", "  ", "Python"])
    assert result == ["hello", "world", "python"]


def test_search_items_functional(workspace_path):
    utils = _load_module(workspace_path, "utils")
    items = ["hello", "world", "hello world", "python"]
    result = utils.search_items(data=items, query="hello")
    assert "hello" in result
    assert "hello world" in result
    assert "python" not in result
