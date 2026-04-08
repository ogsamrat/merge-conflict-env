"""
Programmatic merge conflict scenario generator.

Creates new conflict scenarios by defining base content and two diverging
branch modifications. Useful for extending the environment with new tasks.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class BranchSpec:
    """Specification for a branch's changes."""
    name: str
    commit_message: str
    files: Dict[str, str]


@dataclass
class ConflictScenario:
    """Full specification for a merge conflict scenario."""
    task_id: str
    difficulty: str
    description: str
    base_files: Dict[str, str]
    branch_a: BranchSpec
    branch_b: BranchSpec
    gold_resolutions: Dict[str, str]
    conflicted_files: list[str] = field(default_factory=list)


def generate_conflict_repo(scenario: ConflictScenario, workspace_dir: str) -> None:
    """Create a git repo with merge conflicts from a scenario spec.

    Args:
        scenario: The conflict scenario to generate.
        workspace_dir: Directory to create the repo in.
    """
    ws = Path(workspace_dir)
    ws.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Dev",
        "GIT_AUTHOR_EMAIL": "dev@test.com",
        "GIT_COMMITTER_NAME": "Dev",
        "GIT_COMMITTER_EMAIL": "dev@test.com",
    }

    def run_git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + list(args),
            cwd=str(ws),
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

    run_git("init")
    run_git("checkout", "-b", "main")

    for fname, content in scenario.base_files.items():
        fpath = ws / fname
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")

    run_git("add", ".")
    run_git("commit", "-m", "Initial commit")

    run_git("checkout", "-b", scenario.branch_a.name)
    for fname, content in scenario.branch_a.files.items():
        (ws / fname).write_text(content, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", scenario.branch_a.commit_message)

    run_git("checkout", "main")
    run_git("checkout", "-b", scenario.branch_b.name)
    for fname, content in scenario.branch_b.files.items():
        (ws / fname).write_text(content, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", scenario.branch_b.commit_message)

    run_git("checkout", scenario.branch_a.name)
    subprocess.run(
        ["git", "merge", scenario.branch_b.name, "--no-edit"],
        cwd=str(ws), capture_output=True, text=True, env=env,
    )


def save_gold_resolutions(scenario: ConflictScenario, gold_dir: str) -> None:
    """Save gold-standard resolutions to a directory."""
    gd = Path(gold_dir)
    gd.mkdir(parents=True, exist_ok=True)
    for fname, content in scenario.gold_resolutions.items():
        (gd / fname).write_text(content, encoding="utf-8")


# ── Example: Generate a custom scenario ──

EXAMPLE_SCENARIO = ConflictScenario(
    task_id="custom_config_conflict",
    difficulty="easy",
    description="Two developers modified the same config file",
    base_files={
        "settings.json": '{\n  "debug": false,\n  "port": 3000,\n  "host": "localhost"\n}\n',
    },
    branch_a=BranchSpec(
        name="update-port",
        commit_message="Change port to 8080",
        files={
            "settings.json": '{\n  "debug": false,\n  "port": 8080,\n  "host": "localhost",\n  "ssl": true\n}\n',
        },
    ),
    branch_b=BranchSpec(
        name="enable-debug",
        commit_message="Enable debug mode and add logging",
        files={
            "settings.json": '{\n  "debug": true,\n  "port": 3000,\n  "host": "localhost",\n  "log_level": "verbose"\n}\n',
        },
    ),
    gold_resolutions={
        "settings.json": '{\n  "debug": true,\n  "port": 8080,\n  "host": "localhost",\n  "ssl": true,\n  "log_level": "verbose"\n}\n',
    },
    conflicted_files=["settings.json"],
)


if __name__ == "__main__":
    import tempfile

    print("Generating example conflict scenario...")
    with tempfile.TemporaryDirectory() as tmp:
        generate_conflict_repo(EXAMPLE_SCENARIO, tmp)

        for fname in EXAMPLE_SCENARIO.base_files:
            fpath = Path(tmp) / fname
            if fpath.exists():
                print(f"\n=== {fname} (with conflicts) ===")
                print(fpath.read_text(encoding="utf-8"))

        gold_dir = Path(tmp) / "gold"
        save_gold_resolutions(EXAMPLE_SCENARIO, str(gold_dir))
        for fname in EXAMPLE_SCENARIO.gold_resolutions:
            print(f"\n=== {fname} (gold resolution) ===")
            print((gold_dir / fname).read_text(encoding="utf-8"))

    print("\nScenario generated successfully!")
