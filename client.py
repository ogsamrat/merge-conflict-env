"""
MergeConflictEnv Client

Client-side wrapper for the Merge Conflict Resolution environment server.
Maintains a persistent WebSocket connection for low-latency interactions.
"""

from __future__ import annotations

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from .models import MergeConflictAction, MergeConflictObservation, MergeConflictState


class MergeConflictEnv(EnvClient[MergeConflictAction, MergeConflictObservation, MergeConflictState]):
    """Client for the Merge Conflict Resolution environment.

    Example:
        >>> client = MergeConflictEnv.from_docker_image("merge-conflict-env:latest")
        >>> try:
        ...     result = client.reset(task_id="easy_simple_text")
        ...     print(result.observation.conflict_files)
        ...
        ...     result = client.step(MergeConflictAction(
        ...         action_type="view_file",
        ...         file_path="README.md",
        ...     ))
        ...     print(result.observation.file_content)
        ...
        ...     result = client.step(MergeConflictAction(
        ...         action_type="resolve_file",
        ...         file_path="README.md",
        ...         content="resolved content here...",
        ...     ))
        ...     print(result.reward)
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: MergeConflictAction) -> dict:
        return {
            "action_type": action.action_type,
            "file_path": action.file_path,
            "content": action.content,
        }

    def _parse_result(self, payload: dict) -> StepResult[MergeConflictObservation]:
        obs = MergeConflictObservation(**payload["observation"])
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=bool(payload.get("done", False)),
        )

    def _parse_state(self, payload: dict) -> MergeConflictState:
        return MergeConflictState(
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", ""),
            difficulty=payload.get("difficulty", ""),
            total_conflicts=payload.get("total_conflicts", 0),
            resolved_conflicts=payload.get("resolved_conflicts", 0),
            total_reward=payload.get("total_reward", 0.0),
            workspace_path=payload.get("workspace_path", ""),
        )
