"""
FastAPI application for the Merge Conflict Resolution Environment.

Custom server that manages a single shared environment instance
for stateful HTTP reset/step/state interactions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

try:
    from merge_conflict_env.models import MergeConflictAction, MergeConflictObservation
    from merge_conflict_env.server.merge_conflict_environment import MergeConflictEnvironment
except ImportError:
    from models import MergeConflictAction, MergeConflictObservation
    from server.merge_conflict_environment import MergeConflictEnvironment


app = FastAPI(
    title="Merge Conflict Resolution Environment",
    description="OpenEnv RL environment for resolving git merge conflicts",
    version="0.1.0",
)

env = MergeConflictEnvironment()


class ResetRequest(BaseModel):
    task_id: str = "easy_simple_text"
    seed: Optional[int] = None
    episode_id: Optional[str] = None


class StepRequest(BaseModel):
    action: Dict[str, Any]
    timeout_s: Optional[float] = None


class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "merge_conflict_env"}


@app.get("/schema")
async def schema():
    return {
        "action": MergeConflictAction.model_json_schema(),
        "observation": MergeConflictObservation.model_json_schema(),
    }


@app.post("/reset")
async def reset(request: Optional[ResetRequest] = None):
    if request is None:
        request = ResetRequest()
    obs = env.reset(
        seed=request.seed,
        episode_id=request.episode_id,
        task_id=request.task_id,
    )
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward if hasattr(obs, "reward") else 0.0,
        "done": obs.done if hasattr(obs, "done") else False,
    }


@app.post("/step")
async def step(request: StepRequest):
    action_data = request.action
    action = MergeConflictAction(**action_data)
    obs = env.step(action, timeout_s=request.timeout_s)
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward if hasattr(obs, "reward") else 0.0,
        "done": obs.done if hasattr(obs, "done") else False,
    }


@app.get("/state")
async def state():
    return env.state.model_dump()


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
