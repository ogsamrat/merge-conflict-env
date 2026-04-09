"""
Medium Task: Import & Validation Conflict

Two developers independently extend a data processor:
  - Branch 'feature-logging': Adds structured logging (import logging) to
    processor.py and pipeline.py.
  - Branch 'feature-validation': Adds regex-based input validation (import re)
    with a new validate() method in processor.py and a filter_valid() helper in
    pipeline.py.

Both branches modify the same lines in both files, creating conflicts in:
  - The module-level import/constant section of processor.py
  - The process() method body of processor.py
  - The run_pipeline() function body of pipeline.py
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# ── Base versions ──────────────────────────────────────────────────────────────

BASE_PROCESSOR = '''\
"""Data processor module."""

STRIP_CHARS = " \\t\\n\\r"


class DataProcessor:
    """Processes text data."""

    def __init__(self, strip: bool = True) -> None:
        self.strip = strip

    def process(self, text: str) -> str:
        """Process and normalize a text string."""
        if self.strip:
            text = text.strip(STRIP_CHARS)
        return text.lower()
'''

BASE_PIPELINE = '''\
"""Batch processing pipeline."""

from processor import DataProcessor


def run_pipeline(texts: list) -> list:
    """Process a batch of texts and return results."""
    dp = DataProcessor()
    return [dp.process(t) for t in texts]
'''

# ── Branch A: feature-logging ─────────────────────────────────────────────────

BRANCH_A_PROCESSOR = '''\
"""Data processor module."""

import logging

STRIP_CHARS = " \\t\\n\\r"

_log = logging.getLogger(__name__)


class DataProcessor:
    """Processes text data."""

    def __init__(self, strip: bool = True) -> None:
        self.strip = strip

    def process(self, text: str) -> str:
        """Process and normalize a text string."""
        _log.debug("process() input: %r", text)
        if self.strip:
            text = text.strip(STRIP_CHARS)
        result = text.lower()
        _log.debug("process() output: %r", result)
        return result
'''

BRANCH_A_PIPELINE = '''\
"""Batch processing pipeline."""

import logging

from processor import DataProcessor

logging.basicConfig(level=logging.WARNING)


def run_pipeline(texts: list) -> list:
    """Process a batch of texts, logging and skipping errors."""
    dp = DataProcessor()
    results = []
    for t in texts:
        try:
            results.append(dp.process(t))
        except Exception as exc:
            logging.warning("Skipping %r: %s", t, exc)
    return results
'''

# ── Branch B: feature-validation ──────────────────────────────────────────────

BRANCH_B_PROCESSOR = '''\
"""Data processor module."""

import re

STRIP_CHARS = " \\t\\n\\r"

_WORD_RE = re.compile(r"\\w+")


class DataProcessor:
    """Processes text data."""

    def __init__(self, strip: bool = True) -> None:
        self.strip = strip

    def validate(self, text: str) -> bool:
        """Return True if text contains at least one word character."""
        return bool(text and _WORD_RE.search(text))

    def process(self, text: str) -> str:
        """Process and normalize a text string."""
        if not self.validate(text):
            raise ValueError(f"Invalid input: {text!r}")
        if self.strip:
            text = text.strip(STRIP_CHARS)
        return text.lower()
'''

BRANCH_B_PIPELINE = '''\
"""Batch processing pipeline."""

from processor import DataProcessor


def run_pipeline(texts: list) -> list:
    """Process valid texts only, silently skipping invalid ones."""
    dp = DataProcessor()
    return [dp.process(t) for t in texts if dp.validate(t)]


def filter_valid(texts: list) -> list:
    """Return only texts that pass DataProcessor.validate()."""
    dp = DataProcessor()
    return [t for t in texts if dp.validate(t)]
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

    (ws / "processor.py").write_text(BASE_PROCESSOR, encoding="utf-8")
    (ws / "pipeline.py").write_text(BASE_PIPELINE, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Initial commit: data processor and pipeline")

    # Branch A: add structured logging
    run_git("checkout", "-b", "feature-logging")
    (ws / "processor.py").write_text(BRANCH_A_PROCESSOR, encoding="utf-8")
    (ws / "pipeline.py").write_text(BRANCH_A_PIPELINE, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Feature: add structured logging to processor and pipeline")

    # Branch B: add input validation
    run_git("checkout", "main")
    run_git("checkout", "-b", "feature-validation")
    (ws / "processor.py").write_text(BRANCH_B_PROCESSOR, encoding="utf-8")
    (ws / "pipeline.py").write_text(BRANCH_B_PIPELINE, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Feature: add regex input validation and filter_valid helper")

    # Merge validation into logging → produces conflicts
    run_git("checkout", "feature-logging")
    subprocess.run(
        ["git", "merge", "feature-validation", "--no-edit"],
        cwd=str(ws), capture_output=True, text=True, env=env,
    )


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        setup_task(tmp)
        for f in ["processor.py", "pipeline.py"]:
            p = Path(tmp) / f
            if p.exists():
                print(f"=== {f} ===")
                print(p.read_text(encoding="utf-8"))
                print()
