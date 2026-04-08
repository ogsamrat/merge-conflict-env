"""Tests for the hard task: multi-file refactor conflict resolution."""

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


def test_no_conflict_markers_all_files(workspace_path):
    for fname in ["config.py", "models.py", "utils.py", "api.py"]:
        content = (Path(workspace_path) / fname).read_text(encoding="utf-8")
        assert "<<<<<<< " not in content, f"Conflict marker in {fname}"
        assert ">>>>>>> " not in content, f"Conflict marker in {fname}"


def test_all_files_valid_python(workspace_path):
    for fname in ["config.py", "models.py", "utils.py", "api.py"]:
        content = (Path(workspace_path) / fname).read_text(encoding="utf-8")
        ast.parse(content)


def test_config_has_dataclass(workspace_path):
    content = (Path(workspace_path) / "config.py").read_text(encoding="utf-8")
    assert "dataclass" in content, "Config should use dataclass from refactor branch"
    assert "AppConfig" in content, "Config should have AppConfig class"


def test_config_has_rate_limit(workspace_path):
    content = (Path(workspace_path) / "config.py").read_text(encoding="utf-8")
    assert "rate_limit" in content.lower() or "RATE_LIMIT" in content, \
        "Config should have rate_limit from feature branch"


def test_models_has_comment_class(workspace_path):
    content = (Path(workspace_path) / "models.py").read_text(encoding="utf-8")
    assert "class Comment" in content, "Models should have Comment class from feature branch"


def test_models_has_dataclass(workspace_path):
    content = (Path(workspace_path) / "models.py").read_text(encoding="utf-8")
    assert "dataclass" in content, "Models should use dataclass from refactor branch"


def test_utils_has_generate_id(workspace_path):
    content = (Path(workspace_path) / "utils.py").read_text(encoding="utf-8")
    assert "def generate_id" in content, "Utils should have generate_id from refactor branch"


def test_utils_has_validate_length(workspace_path):
    content = (Path(workspace_path) / "utils.py").read_text(encoding="utf-8")
    assert "def validate_length" in content, "Utils should have validate_length from feature branch"


def test_utils_has_type_hints(workspace_path):
    content = (Path(workspace_path) / "utils.py").read_text(encoding="utf-8")
    assert "-> bool" in content or "-> str" in content, "Utils should have type hints from refactor"


def test_api_has_create_comment(workspace_path):
    content = (Path(workspace_path) / "api.py").read_text(encoding="utf-8")
    assert "def create_comment" in content, "API should have create_comment from feature branch"


def test_api_imports_comment(workspace_path):
    content = (Path(workspace_path) / "api.py").read_text(encoding="utf-8")
    assert "Comment" in content, "API should import Comment model"


def test_api_uses_config_object(workspace_path):
    content = (Path(workspace_path) / "api.py").read_text(encoding="utf-8")
    assert "config.max_items" in content or "config." in content, \
        "API should use config object from refactor branch"


def test_api_imports_validate_length(workspace_path):
    content = (Path(workspace_path) / "api.py").read_text(encoding="utf-8")
    assert "validate_length" in content, "API should import validate_length from feature branch"


def test_create_user_functional(workspace_path):
    _load_module(workspace_path, "config")
    _load_module(workspace_path, "models")
    _load_module(workspace_path, "utils")
    api = _load_module(workspace_path, "api")

    result = api.create_user("Alice", "alice@example.com")
    assert "name" in result
    assert result["name"] == "alice"
    assert "email" in result


def test_create_user_invalid_email(workspace_path):
    _load_module(workspace_path, "config")
    _load_module(workspace_path, "models")
    _load_module(workspace_path, "utils")
    api = _load_module(workspace_path, "api")

    result = api.create_user("Bob", "not-an-email")
    assert "error" in result
