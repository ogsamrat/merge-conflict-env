"""
FastAPI application for the Merge Conflict Resolution Environment.

Uses the official OpenEnv create_app for correct serialization,
schema, health, metadata, and step response formatting.
"""

import logging

from openenv.core.env_server import create_app

try:
    from merge_conflict_env.models import MergeConflictAction, MergeConflictObservation
    from merge_conflict_env.server.merge_conflict_environment import (
        MergeConflictEnvironment,
    )
except ImportError:
    from models import MergeConflictAction, MergeConflictObservation
    from server.merge_conflict_environment import MergeConflictEnvironment

logger = logging.getLogger(__name__)

_env_instance = MergeConflictEnvironment()


def create_merge_conflict_environment():
    """Factory that returns the singleton environment instance."""
    return _env_instance


app = create_app(
    create_merge_conflict_environment,
    MergeConflictAction,
    MergeConflictObservation,
    env_name="merge_conflict_env",
)


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
