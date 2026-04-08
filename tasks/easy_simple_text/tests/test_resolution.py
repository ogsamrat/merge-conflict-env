"""Tests for the easy task: simple text conflict resolution."""

from pathlib import Path


def test_no_conflict_markers(workspace_path):
    readme = Path(workspace_path) / "README.md"
    assert readme.exists(), "README.md must exist"
    content = readme.read_text(encoding="utf-8")
    assert "<<<<<<< " not in content, "Conflict start marker found"
    assert ">>>>>>> " not in content, "Conflict end marker found"
    for line in content.splitlines():
        assert line.strip() != "=" * 7, "Conflict separator (=======) found"


def test_has_installation_section(workspace_path):
    content = (Path(workspace_path) / "README.md").read_text(encoding="utf-8")
    assert "## Installation" in content, "Missing Installation section from feature-install branch"
    assert "pip install myproject" in content, "Missing pip install command"


def test_has_setup_guide_section(workspace_path):
    content = (Path(workspace_path) / "README.md").read_text(encoding="utf-8")
    assert "## Setup Guide" in content, "Missing Setup Guide section from feature-setup branch"
    assert "MYPROJECT_ENV" in content, "Missing environment variable documentation"


def test_has_usage_section(workspace_path):
    content = (Path(workspace_path) / "README.md").read_text(encoding="utf-8")
    assert "## Usage" in content, "Missing Usage section"
    assert "from myproject import process" in content, "Missing usage example"


def test_has_project_title(workspace_path):
    content = (Path(workspace_path) / "README.md").read_text(encoding="utf-8")
    assert content.startswith("# MyProject"), "Missing project title"
