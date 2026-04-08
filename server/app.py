"""
FastAPI application for the Merge Conflict Resolution Environment.

Custom server that manages a single shared environment instance
for stateful HTTP reset/step/state interactions.

Response format matches the official OpenEnv serialize_observation:
  - "observation" dict EXCLUDES reward, done, metadata
  - "reward" and "done" are top-level only
"""

from __future__ import annotations

import json as _json
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

try:
    from merge_conflict_env.grader import (
        MAX_SIMILARITY_REWARD,
        MAX_TEST_REWARD,
        MARKER_REMOVAL_REWARD,
        SCORE_FLOOR,
        SYNTAX_VALID_REWARD,
        clamp_reward,
    )
    from merge_conflict_env.models import (
        MergeConflictAction,
        MergeConflictObservation,
        MergeConflictState,
    )
    from merge_conflict_env.server.merge_conflict_environment import (
        MergeConflictEnvironment,
    )
except ImportError:
    from grader import (
        MAX_SIMILARITY_REWARD,
        MAX_TEST_REWARD,
        MARKER_REMOVAL_REWARD,
        SCORE_FLOOR,
        SYNTAX_VALID_REWARD,
        clamp_reward,
    )
    from models import (
        MergeConflictAction,
        MergeConflictObservation,
        MergeConflictState,
    )
    from server.merge_conflict_environment import MergeConflictEnvironment


app = FastAPI(
    title="Merge Conflict Resolution Environment",
    description="OpenEnv RL environment for resolving git merge conflicts",
    version="0.1.0",
)

env = MergeConflictEnvironment()

_PER_FILE_MAX = MARKER_REMOVAL_REWARD + SYNTAX_VALID_REWARD + MAX_SIMILARITY_REWARD


def _max_episode_reward(n_files: int) -> float:
    return n_files * _PER_FILE_MAX + MAX_TEST_REWARD


def _normalized_score(total_reward: float, n_files: int) -> float:
    max_r = _max_episode_reward(n_files)
    if max_r <= 0:
        return SCORE_FLOOR
    return clamp_reward(total_reward / max_r)


def _serialize(obs: MergeConflictObservation, reward_override: float | None = None):
    """Serialize observation matching official OpenEnv format.

    Excludes reward/done/metadata from obs dict — they go top-level only.
    """
    reward = clamp_reward(
        reward_override if reward_override is not None
        else (obs.reward if obs.reward is not None else SCORE_FLOOR)
    )
    obs_dict = obs.model_dump(exclude={"reward", "done", "metadata"})
    return {
        "observation": obs_dict,
        "reward": reward,
        "done": bool(obs.done),
    }


class ResetRequest(BaseModel):
    task_id: str = "easy_simple_text"
    seed: Optional[int] = None
    episode_id: Optional[str] = None


class StepRequest(BaseModel):
    action: Dict[str, Any] = {}
    timeout_s: Optional[float] = None


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "merge_conflict_env"}


@app.get("/metadata")
async def metadata():
    return {
        "name": "merge-conflict-env",
        "description": (
            "An OpenEnv RL environment where agents resolve git merge conflicts "
            "across three difficulty levels: easy (1 file), medium (2 files), "
            "and hard (4 files). Agents list conflicts, view file content, "
            "examine git context, write resolutions, and run tests."
        ),
        "version": "0.1.0",
        "author": "xamrat",
        "tasks": ["easy_simple_text", "medium_code_logic", "hard_multi_file"],
    }


@app.get("/schema")
async def schema():
    return {
        "action": MergeConflictAction.model_json_schema(),
        "observation": MergeConflictObservation.model_json_schema(),
        "state": MergeConflictState.model_json_schema(),
    }


@app.post("/reset")
async def reset(raw_request: Request):
    try:
        body = await raw_request.body()
        if body and body.strip():
            data = _json.loads(body)
            req = ResetRequest(**data)
        else:
            req = ResetRequest()
        obs = env.reset(
            seed=req.seed,
            episode_id=req.episode_id,
            task_id=req.task_id,
        )
        return _serialize(obs)
    except Exception as exc:
        obs = MergeConflictObservation(
            success=False,
            message=f"Reset failed: {exc}",
            error=str(exc),
            done=False,
            reward=SCORE_FLOOR,
        )
        return _serialize(obs)


@app.post("/step")
async def step(raw_request: Request):
    try:
        body = await raw_request.body()
        data = _json.loads(body) if body and body.strip() else {}
        if "action" not in data and "action_type" in data:
            data = {"action": data}
        req = StepRequest(**data)
        action_data = req.action or {}
        action = MergeConflictAction(**action_data)
        obs = env.step(action, timeout_s=req.timeout_s)

        if obs.done:
            n_files = len(env._task_config.get("files", ["_"]))
            task_score = _normalized_score(env.state.total_reward, n_files)
            return _serialize(obs, reward_override=task_score)

        return _serialize(obs)
    except Exception as exc:
        obs = MergeConflictObservation(
            success=False,
            message=f"Step failed: {exc}",
            error=str(exc),
            done=False,
            reward=SCORE_FLOOR,
        )
        return _serialize(obs)


@app.get("/state")
async def state():
    data = env.state.model_dump()
    n_files = len(env._task_config.get("files", ["_"])) if env._task_config else 1
    data["total_reward"] = clamp_reward(data.get("total_reward", SCORE_FLOOR))
    data["normalized_score"] = _normalized_score(env.state.total_reward, n_files)
    return data


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
