"""
Data models for the Merge Conflict Resolution Environment.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


class MergeConflictAction(Action):
    """Action for interacting with the merge conflict environment.

    Supported action_type values:
        - "list_conflicts": List all files with unresolved conflicts
        - "view_file": View the content of a specific file (with conflict markers)
        - "view_context": View git log, branch names, and commit messages
        - "resolve_file": Submit resolved content for a specific file
        - "run_tests": Run the test suite to verify resolutions
        - "submit": Finalize and submit all resolutions (ends episode)
    """

    action_type: str = Field(
        default="list_conflicts",
        description="Type of action to perform",
    )
    file_path: str = Field(
        default="",
        description="Target file path (for view_file, resolve_file)",
    )
    content: str = Field(
        default="",
        description="Resolved file content (for resolve_file)",
    )


class MergeConflictObservation(Observation):
    """Observation returned from the merge conflict environment."""

    success: bool = Field(default=True, description="Whether the action succeeded")
    message: str = Field(default="", description="Human-readable status message")
    error: str = Field(default="", description="Error message if action failed")

    conflict_files: List[str] = Field(
        default_factory=list,
        description="List of file paths with unresolved conflicts",
    )
    file_content: str = Field(
        default="",
        description="Content of the requested file (may include conflict markers)",
    )
    git_context: str = Field(
        default="",
        description="Git log, branch names, and commit context",
    )
    test_output: str = Field(
        default="",
        description="Output from running the test suite",
    )
    resolution_status: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of file_path -> 'resolved' | 'unresolved'",
    )
    conflicts_remaining: int = Field(
        default=0,
        description="Number of files still containing conflict markers",
    )
    task_id: str = Field(default="", description="Current task identifier")
    difficulty: str = Field(default="", description="Task difficulty: easy, medium, hard")
    info: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MergeConflictState(State):
    """Server-side state tracking for the merge conflict environment."""

    task_id: str = Field(default="", description="Current task identifier")
    difficulty: str = Field(default="", description="easy / medium / hard")
    total_conflicts: int = Field(default=0, description="Total number of conflicted files")
    resolved_conflicts: int = Field(default=0, description="Files resolved so far")
    total_reward: float = Field(default=0.0, description="Accumulated reward this episode")
    workspace_path: str = Field(default="/workspace", description="Path to working git repo")
