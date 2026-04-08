"""
Grading logic for merge conflict resolutions.

Provides incremental, per-file reward scoring:
  - Conflict marker removal check
  - Syntax validation (for Python files)
  - Content similarity against gold-standard resolution
  - Test suite pass rate
"""

from __future__ import annotations

import ast
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Tuple

CONFLICT_MARKERS = ("<<<<<<< ", "=======", ">>>>>>> ")

MARKER_REMOVAL_REWARD = 0.1
SYNTAX_VALID_REWARD = 0.1
MAX_SIMILARITY_REWARD = 0.6
MAX_TEST_REWARD = 0.1
EXPLORATION_REWARD = 0.02
STEP_PENALTY_THRESHOLD = 15
STEP_PENALTY = 0.05
INVALID_ACTION_PENALTY = 0.1


def has_conflict_markers(content: str) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("<<<<<<< ") or stripped.startswith(">>>>>>> "):
            return True
        if stripped == "=" * 7:
            return True
    return False


def count_conflict_blocks(content: str) -> int:
    return sum(1 for line in content.splitlines() if line.strip().startswith("<<<<<<< "))


def is_python_file(file_path: str) -> bool:
    return file_path.endswith(".py")


def is_syntactically_valid_python(content: str) -> bool:
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def compute_similarity(resolved: str, gold: str) -> float:
    return SequenceMatcher(None, resolved.strip(), gold.strip()).ratio()


def grade_resolution(
    resolved_content: str,
    gold_content: str,
    file_path: str,
) -> Tuple[float, Dict[str, float]]:
    """Grade a single file's resolution against the gold standard.

    Returns:
        (total_score, breakdown_dict) where breakdown shows each component.
    """
    breakdown: Dict[str, float] = {}
    score = 0.0

    markers_present = has_conflict_markers(resolved_content)
    if not markers_present:
        score += MARKER_REMOVAL_REWARD
        breakdown["markers_removed"] = MARKER_REMOVAL_REWARD
    else:
        breakdown["markers_removed"] = 0.0

    if is_python_file(file_path):
        if is_syntactically_valid_python(resolved_content):
            score += SYNTAX_VALID_REWARD
            breakdown["syntax_valid"] = SYNTAX_VALID_REWARD
        else:
            breakdown["syntax_valid"] = 0.0
    else:
        score += SYNTAX_VALID_REWARD
        breakdown["syntax_valid"] = SYNTAX_VALID_REWARD

    similarity = compute_similarity(resolved_content, gold_content)
    sim_reward = similarity * MAX_SIMILARITY_REWARD
    score += sim_reward
    breakdown["similarity"] = round(sim_reward, 4)
    breakdown["similarity_ratio"] = round(similarity, 4)

    return round(score, 4), breakdown


def grade_test_run(test_dir: str, workspace_path: str) -> Tuple[float, str]:
    """Run pytest on the task's test suite and return (reward, output)."""
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest", test_dir,
                "-v", "--tb=short",
                f"--workspace-path={workspace_path}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=workspace_path,
        )
        output = result.stdout + result.stderr

        if result.returncode == 0:
            return MAX_TEST_REWARD, output

        lines = output.splitlines()
        for line in reversed(lines):
            if "passed" in line and "failed" in line:
                parts = line.split()
                try:
                    passed_idx = parts.index("passed") - 1
                    failed_idx = parts.index("failed") - 1
                    passed = int(parts[passed_idx])
                    failed = int(parts[failed_idx])
                    total = passed + failed
                    if total > 0:
                        ratio = passed / total
                        return round(ratio * MAX_TEST_REWARD, 4), output
                except (ValueError, IndexError):
                    pass
            elif "passed" in line:
                return MAX_TEST_REWARD, output

        return 0.0, output

    except subprocess.TimeoutExpired:
        return 0.0, "Test execution timed out (30s limit)"
    except Exception as e:
        return 0.0, f"Test execution failed: {e}"


def compute_step_penalty(step_count: int) -> float:
    if step_count > STEP_PENALTY_THRESHOLD:
        return STEP_PENALTY * (step_count - STEP_PENALTY_THRESHOLD)
    return 0.0
