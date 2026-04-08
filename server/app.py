"""
FastAPI application for the Merge Conflict Resolution Environment.

Endpoints:
    - POST /reset: Reset the environment (with task_id param)
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - GET /health: Health check
    - WS /ws: WebSocket endpoint for persistent sessions
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core"
    ) from e

try:
    from merge_conflict_env.models import MergeConflictAction, MergeConflictObservation
    from merge_conflict_env.server.merge_conflict_environment import MergeConflictEnvironment
except ImportError:
    from models import MergeConflictAction, MergeConflictObservation
    from server.merge_conflict_environment import MergeConflictEnvironment


from fastapi.responses import RedirectResponse

app = create_app(
    MergeConflictEnvironment,
    MergeConflictAction,
    MergeConflictObservation,
    env_name="merge_conflict_env",
    max_concurrent_envs=1,
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
