"""
FastAPI application for the Merge Conflict Resolution Environment.

Uses the official OpenEnv create_app for correct serialization and session management.
Supports concurrent WebSocket sessions; each session gets its own environment instance.
"""

import logging
import os

from openenv.core.env_server import create_app

try:
    from openenv.core.env_server import create_web_interface_app
    _HAS_WEB = True
except ImportError:
    _HAS_WEB = False

try:
    from merge_conflict_env.models import MergeConflictAction, MergeConflictObservation
    from merge_conflict_env.server.merge_conflict_environment import MergeConflictEnvironment
except ImportError:
    from models import MergeConflictAction, MergeConflictObservation
    from server.merge_conflict_environment import MergeConflictEnvironment

logger = logging.getLogger(__name__)

MAX_CONCURRENT_ENVS = int(os.environ.get("MAX_CONCURRENT_ENVS", "8"))
ENABLE_WEB_INTERFACE = os.environ.get("ENABLE_WEB_INTERFACE", "true").lower() == "true"
ENV_NAME = "merge_conflict_env"


def create_environment() -> MergeConflictEnvironment:
    """Factory: each WebSocket session gets a fresh, isolated environment."""
    return MergeConflictEnvironment()


if _HAS_WEB and ENABLE_WEB_INTERFACE:
    try:
        app = create_web_interface_app(
            create_environment,
            MergeConflictAction,
            MergeConflictObservation,
            env_name=ENV_NAME,
            max_concurrent_envs=MAX_CONCURRENT_ENVS,
        )
        logger.info("Web interface enabled at /web")
    except Exception:
        ENABLE_WEB_INTERFACE = False

if not (ENABLE_WEB_INTERFACE and _HAS_WEB):
    app = create_app(
        create_environment,
        MergeConflictAction,
        MergeConflictObservation,
        env_name=ENV_NAME,
        max_concurrent_envs=MAX_CONCURRENT_ENVS,
    )


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
