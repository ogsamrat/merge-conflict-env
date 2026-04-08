"""
Medium Task: Code Function Conflict

Creates a git repo with merge conflicts across 2 Python files.
- Branch 'refactor-types': Renames function params and adds type hints to utils.py
- Branch 'feature-search': Adds a search feature in main.py that calls the utility
- Merging produces 3 conflict blocks across utils.py and main.py.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# ── Base versions ──

BASE_UTILS = '''\
"""Utility functions for data processing."""


def process_items(items, filter_fn=None):
    """Process a list of items with an optional filter.

    Args:
        items: List of items to process.
        filter_fn: Optional filter function.

    Returns:
        List of processed items.
    """
    if filter_fn:
        items = [item for item in items if filter_fn(item)]

    results = []
    for item in items:
        cleaned = item.strip().lower()
        if cleaned:
            results.append(cleaned)
    return results


def format_output(items, separator=", "):
    """Format items into a single string."""
    return separator.join(str(item) for item in items)
'''

BASE_MAIN = '''\
"""Main module for MyProject."""

from utils import process_items, format_output


def run_pipeline(raw_data):
    """Run the full processing pipeline."""
    processed = process_items(raw_data)
    return format_output(processed)


if __name__ == "__main__":
    data = ["  Hello ", "World  ", "  ", "Python"]
    print(run_pipeline(data))
'''

# ── Branch A: refactor-types ──

BRANCH_A_UTILS = '''\
"""Utility functions for data processing."""

from typing import Callable, List, Optional


def process_items(
    data: List[str],
    predicate: Optional[Callable[[str], bool]] = None,
) -> List[str]:
    """Process a list of string items with an optional predicate filter.

    Args:
        data: List of string items to process.
        predicate: Optional predicate function to filter items.

    Returns:
        List of cleaned, non-empty string items.
    """
    if predicate:
        data = [item for item in data if predicate(item)]

    results: List[str] = []
    for item in data:
        cleaned = item.strip().lower()
        if cleaned:
            results.append(cleaned)
    return results


def format_output(data: List[str], separator: str = ", ") -> str:
    """Format items into a single string."""
    return separator.join(str(item) for item in data)
'''

BRANCH_A_MAIN = '''\
"""Main module for MyProject."""

from utils import process_items, format_output


def run_pipeline(raw_data: list[str]) -> str:
    """Run the full processing pipeline."""
    processed = process_items(data=raw_data)
    return format_output(data=processed)


if __name__ == "__main__":
    data = ["  Hello ", "World  ", "  ", "Python"]
    print(run_pipeline(data))
'''

# ── Branch B: feature-search ──

BRANCH_B_UTILS = '''\
"""Utility functions for data processing."""


def process_items(items, filter_fn=None):
    """Process a list of items with an optional filter.

    Args:
        items: List of items to process.
        filter_fn: Optional filter function.

    Returns:
        List of processed items.
    """
    if filter_fn:
        items = [item for item in items if filter_fn(item)]

    results = []
    for item in items:
        cleaned = item.strip().lower()
        if cleaned:
            results.append(cleaned)
    return results


def format_output(items, separator=", "):
    """Format items into a single string."""
    return separator.join(str(item) for item in items)


def search_items(items, query):
    """Search for items matching a query string.

    Args:
        items: List of items to search through.
        query: Search query string.

    Returns:
        List of items containing the query.
    """
    query_lower = query.strip().lower()
    return [item for item in items if query_lower in item.strip().lower()]
'''

BRANCH_B_MAIN = '''\
"""Main module for MyProject."""

from utils import process_items, format_output, search_items


def run_pipeline(raw_data):
    """Run the full processing pipeline."""
    processed = process_items(raw_data)
    return format_output(processed)


def run_search(raw_data, query):
    """Search through processed data."""
    processed = process_items(raw_data)
    matches = search_items(processed, query)
    return format_output(matches)


if __name__ == "__main__":
    data = ["  Hello ", "World  ", "  ", "Python", "Hello World"]
    print(run_pipeline(data))
    print("Search results:", run_search(data, "hello"))
'''


def setup_task(workspace_dir: str) -> None:
    """Create the conflicted git repo in workspace_dir."""
    ws = Path(workspace_dir)
    ws.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Dev",
        "GIT_AUTHOR_EMAIL": "dev@test.com",
        "GIT_COMMITTER_NAME": "Dev",
        "GIT_COMMITTER_EMAIL": "dev@test.com",
    }

    def run_git(*args: str) -> None:
        subprocess.run(
            ["git"] + list(args), cwd=str(ws),
            capture_output=True, text=True, check=True, env=env,
        )

    run_git("init")
    run_git("checkout", "-b", "main")

    (ws / "utils.py").write_text(BASE_UTILS, encoding="utf-8")
    (ws / "main.py").write_text(BASE_MAIN, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Initial commit: add utils.py and main.py")

    run_git("checkout", "-b", "refactor-types")
    (ws / "utils.py").write_text(BRANCH_A_UTILS, encoding="utf-8")
    (ws / "main.py").write_text(BRANCH_A_MAIN, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Refactor: add type hints and rename params for clarity")

    run_git("checkout", "main")
    run_git("checkout", "-b", "feature-search")
    (ws / "utils.py").write_text(BRANCH_B_UTILS, encoding="utf-8")
    (ws / "main.py").write_text(BRANCH_B_MAIN, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Feature: add search_items utility and run_search pipeline")

    run_git("checkout", "refactor-types")
    subprocess.run(
        ["git", "merge", "feature-search", "--no-edit"],
        cwd=str(ws), capture_output=True, text=True, env=env,
    )


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        setup_task(tmp)
        for f in ["utils.py", "main.py"]:
            p = Path(tmp) / f
            if p.exists():
                print(f"=== {f} ===")
                print(p.read_text(encoding="utf-8"))
