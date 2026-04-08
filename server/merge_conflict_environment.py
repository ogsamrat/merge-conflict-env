"""
Merge Conflict Resolution Environment.

Core environment implementation following the OpenEnv Environment interface.
Manages task lifecycle: setup conflicted repos, handle agent actions,
compute incremental rewards, and track state.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from merge_conflict_env.models import (
        MergeConflictAction,
        MergeConflictObservation,
        MergeConflictState,
    )
    from merge_conflict_env.grader import (
        EXPLORATION_REWARD,
        INVALID_ACTION_PENALTY,
        compute_step_penalty,
        grade_resolution,
        grade_test_run,
        has_conflict_markers,
    )
except ImportError:
    from models import (
        MergeConflictAction,
        MergeConflictObservation,
        MergeConflictState,
    )
    from grader import (
        EXPLORATION_REWARD,
        INVALID_ACTION_PENALTY,
        compute_step_penalty,
        grade_resolution,
        grade_test_run,
        has_conflict_markers,
    )

TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"

TASK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "easy_simple_text": {
        "difficulty": "easy",
        "setup_module": "merge_conflict_env.tasks.easy_simple_text.setup",
        "gold_dir": TASKS_DIR / "easy_simple_text" / "gold_resolution",
        "test_dir": TASKS_DIR / "easy_simple_text" / "tests",
        "files": ["README.md"],
        "description": "Simple text conflict in a README file (1 file, 1 conflict block)",
    },
    "medium_code_logic": {
        "difficulty": "medium",
        "setup_module": "merge_conflict_env.tasks.medium_code_logic.setup",
        "gold_dir": TASKS_DIR / "medium_code_logic" / "gold_resolution",
        "test_dir": TASKS_DIR / "medium_code_logic" / "tests",
        "files": ["utils.py", "main.py"],
        "description": "Code function conflict across 2 files (2 files, 3 conflict blocks)",
    },
    "hard_multi_file": {
        "difficulty": "hard",
        "setup_module": "merge_conflict_env.tasks.hard_multi_file.setup",
        "gold_dir": TASKS_DIR / "hard_multi_file" / "gold_resolution",
        "test_dir": TASKS_DIR / "hard_multi_file" / "tests",
        "files": ["config.py", "models.py", "utils.py", "api.py"],
        "description": "Multi-file refactor conflict (4 files, 5-6 conflict blocks)",
    },
}


class MergeConflictEnvironment(
    Environment[MergeConflictAction, MergeConflictObservation, MergeConflictState]
):
    """OpenEnv environment for merge conflict resolution tasks.

    Agents observe conflicted files, examine git context,
    resolve conflicts file-by-file, and receive incremental rewards.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, workspace_base: str | None = None):
        super().__init__()
        self._workspace_base = workspace_base or os.getenv("WORKSPACE_DIR", "/workspace")
        self._state = MergeConflictState()
        self._task_config: Dict[str, Any] = {}
        self._gold_contents: Dict[str, str] = {}
        self._file_resolved: Dict[str, bool] = {}
        self._workspace: str = ""
        self._git_context_cache: str = ""

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        **kwargs: Any,
    ) -> MergeConflictObservation:
        task_id = kwargs.get("task_id", "easy_simple_text")

        if task_id not in TASK_REGISTRY:
            available = ", ".join(TASK_REGISTRY.keys())
            return MergeConflictObservation(
                success=False,
                message=f"Unknown task_id: {task_id}",
                error=f"Available tasks: {available}",
                done=False,
                reward=0.0,
            )

        self._task_config = TASK_REGISTRY[task_id]
        eid = episode_id or uuid4().hex[:12]
        self._workspace = os.path.join(self._workspace_base, f"{task_id}_{eid}")

        if os.path.exists(self._workspace):
            shutil.rmtree(self._workspace)

        try:
            self._run_task_setup(task_id)
        except Exception as e:
            return MergeConflictObservation(
                success=False,
                message="Failed to set up task",
                error=str(e),
                done=False,
                reward=0.0,
            )

        self._gold_contents = self._load_gold_resolutions()
        self._file_resolved = {f: False for f in self._task_config["files"]}
        self._git_context_cache = ""

        conflict_files = self._find_conflict_files()

        self._state = MergeConflictState(
            episode_id=eid,
            step_count=0,
            task_id=task_id,
            difficulty=self._task_config["difficulty"],
            total_conflicts=len(conflict_files),
            resolved_conflicts=0,
            total_reward=0.0,
            workspace_path=self._workspace,
        )

        return MergeConflictObservation(
            success=True,
            message=f"Task '{task_id}' ready. {self._task_config['description']}",
            conflict_files=conflict_files,
            conflicts_remaining=len(conflict_files),
            resolution_status={f: "unresolved" for f in conflict_files},
            task_id=task_id,
            difficulty=self._task_config["difficulty"],
            done=False,
            reward=0.0,
            info={"available_actions": ["list_conflicts", "view_file", "view_context", "resolve_file", "run_tests", "submit"]},
        )

    def step(
        self,
        action: MergeConflictAction,
        timeout_s: float | None = None,
        **kwargs: Any,
    ) -> MergeConflictObservation:
        if not isinstance(action, MergeConflictAction):
            raise TypeError(f"Expected MergeConflictAction, got {type(action)}")

        if not self._workspace or not os.path.exists(self._workspace):
            return MergeConflictObservation(
                success=False,
                message="Environment not initialized. Call reset() first.",
                error="No active workspace",
                done=False,
                reward=0.0,
            )

        self._state.step_count += 1

        step_penalty = compute_step_penalty(self._state.step_count)

        try:
            if action.action_type == "list_conflicts":
                obs = self._handle_list_conflicts()
            elif action.action_type == "view_file":
                obs = self._handle_view_file(action.file_path)
            elif action.action_type == "view_context":
                obs = self._handle_view_context()
            elif action.action_type == "resolve_file":
                obs = self._handle_resolve_file(action.file_path, action.content)
            elif action.action_type == "run_tests":
                obs = self._handle_run_tests()
            elif action.action_type == "submit":
                obs = self._handle_submit()
            else:
                obs = MergeConflictObservation(
                    success=False,
                    message=f"Unknown action_type: {action.action_type}",
                    error="Valid types: list_conflicts, view_file, view_context, resolve_file, run_tests, submit",
                    reward=-INVALID_ACTION_PENALTY,
                )
        except Exception as e:
            obs = MergeConflictObservation(
                success=False,
                message=f"Action failed: {e}",
                error=str(e),
                reward=-INVALID_ACTION_PENALTY,
            )

        if step_penalty > 0 and obs.reward >= 0:
            obs.reward = round(max(obs.reward - step_penalty, -0.1), 4)

        self._state.total_reward = round(self._state.total_reward + obs.reward, 4)

        return obs

    @property
    def state(self) -> MergeConflictState:
        return self._state

    def close(self) -> None:
        if self._workspace and os.path.exists(self._workspace):
            shutil.rmtree(self._workspace, ignore_errors=True)
        self._workspace = ""

    # ── Action handlers ──

    def _handle_list_conflicts(self) -> MergeConflictObservation:
        conflict_files = self._find_conflict_files()
        status = self._get_resolution_status()
        return MergeConflictObservation(
            success=True,
            message=f"{len(conflict_files)} file(s) with unresolved conflicts",
            conflict_files=conflict_files,
            conflicts_remaining=len(conflict_files),
            resolution_status=status,
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,
            done=False,
            reward=EXPLORATION_REWARD,
        )

    def _handle_view_file(self, file_path: str) -> MergeConflictObservation:
        if not file_path:
            return MergeConflictObservation(
                success=False,
                message="file_path is required for view_file",
                error="Missing file_path",
                reward=-INVALID_ACTION_PENALTY,
            )

        full_path = Path(self._workspace) / file_path
        if not full_path.exists():
            available = [f for f in self._task_config["files"]]
            return MergeConflictObservation(
                success=False,
                message=f"File not found: {file_path}",
                error=f"Available files: {available}",
                reward=-INVALID_ACTION_PENALTY,
            )

        content = full_path.read_text(encoding="utf-8")
        return MergeConflictObservation(
            success=True,
            message=f"Content of {file_path} ({len(content)} chars)",
            file_content=content,
            conflict_files=self._find_conflict_files(),
            resolution_status=self._get_resolution_status(),
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,
            done=False,
            reward=EXPLORATION_REWARD,
        )

    def _handle_view_context(self) -> MergeConflictObservation:
        if not self._git_context_cache:
            self._git_context_cache = self._build_git_context()

        return MergeConflictObservation(
            success=True,
            message="Git context for this merge conflict",
            git_context=self._git_context_cache,
            conflict_files=self._find_conflict_files(),
            resolution_status=self._get_resolution_status(),
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,
            done=False,
            reward=EXPLORATION_REWARD,
        )

    def _handle_resolve_file(self, file_path: str, content: str) -> MergeConflictObservation:
        if not file_path:
            return MergeConflictObservation(
                success=False,
                message="file_path is required for resolve_file",
                error="Missing file_path",
                reward=-INVALID_ACTION_PENALTY,
            )

        if not content:
            return MergeConflictObservation(
                success=False,
                message="content is required for resolve_file",
                error="Missing content",
                reward=-INVALID_ACTION_PENALTY,
            )

        full_path = Path(self._workspace) / file_path
        if not full_path.exists() and file_path not in self._task_config["files"]:
            return MergeConflictObservation(
                success=False,
                message=f"File not found: {file_path}",
                error="Invalid file_path",
                reward=-INVALID_ACTION_PENALTY,
            )

        gold = self._gold_contents.get(file_path, "")
        score, breakdown = grade_resolution(content, gold, file_path)

        full_path.write_text(content, encoding="utf-8")

        is_resolved = not has_conflict_markers(content)
        self._file_resolved[file_path] = is_resolved

        if is_resolved:
            self._state.resolved_conflicts = sum(1 for v in self._file_resolved.values() if v)

        conflict_files = self._find_conflict_files()

        return MergeConflictObservation(
            success=True,
            message=f"Resolved {file_path} (score: {score:.2f})",
            conflict_files=conflict_files,
            conflicts_remaining=len(conflict_files),
            resolution_status=self._get_resolution_status(),
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,
            done=False,
            reward=round(score, 4),
            info={"grading_breakdown": breakdown},
        )

    def _handle_run_tests(self) -> MergeConflictObservation:
        test_dir = str(self._task_config["test_dir"])
        conftest_src = TASKS_DIR / "conftest.py"
        conftest_dst = Path(self._workspace) / "conftest.py"
        if conftest_src.exists() and not conftest_dst.exists():
            shutil.copy2(str(conftest_src), str(conftest_dst))

        reward, output = grade_test_run(test_dir, self._workspace)

        return MergeConflictObservation(
            success=reward > 0,
            message=f"Tests {'passed' if reward > 0 else 'failed'} (reward: {reward:.2f})",
            test_output=output,
            conflict_files=self._find_conflict_files(),
            resolution_status=self._get_resolution_status(),
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,
            done=False,
            reward=round(reward, 4),
        )

    def _handle_submit(self) -> MergeConflictObservation:
        conflict_files = self._find_conflict_files()
        status = self._get_resolution_status()

        total_score = self._state.total_reward
        unresolved = len(conflict_files)

        if unresolved > 0:
            message = f"Submitted with {unresolved} unresolved conflict(s). Total reward: {total_score:.2f}"
        else:
            message = f"All conflicts resolved! Total reward: {total_score:.2f}"

        return MergeConflictObservation(
            success=unresolved == 0,
            message=message,
            conflict_files=conflict_files,
            conflicts_remaining=unresolved,
            resolution_status=status,
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,
            done=True,
            reward=0.0,
            info={"total_episode_reward": total_score},
        )

    # ── Internal helpers ──

    def _run_task_setup(self, task_id: str) -> None:
        setup_module_name = self._task_config["setup_module"]
        try:
            mod = importlib.import_module(setup_module_name)
        except ImportError:
            fallback = setup_module_name.replace("merge_conflict_env.", "")
            mod = importlib.import_module(fallback)

        mod.setup_task(self._workspace)

    def _load_gold_resolutions(self) -> Dict[str, str]:
        gold_dir = self._task_config["gold_dir"]
        contents: Dict[str, str] = {}
        for fname in self._task_config["files"]:
            gold_path = gold_dir / fname
            if gold_path.exists():
                contents[fname] = gold_path.read_text(encoding="utf-8")
        return contents

    def _find_conflict_files(self) -> List[str]:
        conflict_files: List[str] = []
        for fname in self._task_config.get("files", []):
            fpath = Path(self._workspace) / fname
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8")
                if has_conflict_markers(content):
                    conflict_files.append(fname)
        return conflict_files

    def _get_resolution_status(self) -> Dict[str, str]:
        status: Dict[str, str] = {}
        for fname in self._task_config.get("files", []):
            fpath = Path(self._workspace) / fname
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8")
                status[fname] = "unresolved" if has_conflict_markers(content) else "resolved"
            else:
                status[fname] = "missing"
        return status

    def _build_git_context(self) -> str:
        parts: List[str] = []

        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--all", "-20"],
                cwd=self._workspace, capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                parts.append("=== Git Log ===")
                parts.append(result.stdout.strip())
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=self._workspace, capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                parts.append("\n=== Branches ===")
                parts.append(result.stdout.strip())
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["git", "log", "--all", "--format=%h %s (%an)", "-10"],
                cwd=self._workspace, capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                parts.append("\n=== Commit Messages ===")
                parts.append(result.stdout.strip())
        except Exception:
            pass

        return "\n".join(parts) if parts else "Git context unavailable"
