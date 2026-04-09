"""Pytest fixtures for expert_functional task tests."""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--workspace-path",
        action="store",
        default=None,
        help="Path to the workspace directory containing resolved files",
    )


@pytest.fixture
def workspace_path(request):
    wp = request.config.getoption("--workspace-path")
    if wp is None:
        pytest.skip("--workspace-path not provided")
    return wp
