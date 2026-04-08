"""
MergeConflictEnv - Merge Conflict Resolution Environment for OpenEnv.

An RL environment where agents resolve real-world git merge conflicts
across increasing difficulty levels: easy (text), medium (code), hard (multi-file).
"""

from .models import MergeConflictAction, MergeConflictObservation, MergeConflictState

try:
    from .client import MergeConflictEnv
except ImportError:
    MergeConflictEnv = None  # type: ignore[assignment, misc]

__all__ = [
    "MergeConflictEnv",
    "MergeConflictAction",
    "MergeConflictObservation",
    "MergeConflictState",
]
