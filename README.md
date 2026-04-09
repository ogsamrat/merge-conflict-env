---
title: Merge Conflict Resolution Environment
emoji: "🔀"
colorFrom: red
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /docs
tags:
  - openenv
  - merge-conflict
  - code-review
  - spaces
---

# Merge Conflict Resolution Environment

An OpenEnv-compliant RL environment where AI agents learn to resolve real-world git merge conflicts. Agents examine conflicted files, understand branch intent through git context, and produce correct resolutions — evaluated with incremental, multi-signal reward functions.

## Overview & Motivation

Merge conflicts are one of the most common and time-consuming challenges in collaborative software development. Every team encounters them, and resolving them correctly requires:

- **Reading code** across multiple files
- **Understanding intent** from commit messages and branch names
- **Synthesizing changes** from diverging branches
- **Maintaining consistency** across files and imports

This environment simulates that process as a sequential decision-making task, making it ideal for training and evaluating RL agents and LLMs.

## Quick Start

```python
from merge_conflict_env import MergeConflictEnv, MergeConflictAction

env = MergeConflictEnv(base_url="http://localhost:8000")

# Start an easy task
result = env.reset(task_id="easy_simple_text")
print(result.observation.conflict_files)  # ['README.md']

# View the conflicted file
result = env.step(MergeConflictAction(
    action_type="view_file",
    file_path="README.md",
))
print(result.observation.file_content)

# Resolve it
result = env.step(MergeConflictAction(
    action_type="resolve_file",
    file_path="README.md",
    content="...resolved content...",
))
print(f"Reward: {result.reward}")  # 0.01 to 0.99

# Run tests to verify
result = env.step(MergeConflictAction(action_type="run_tests"))

# Submit
result = env.step(MergeConflictAction(action_type="submit"))
print(f"Done: {result.done}")  # True
```

## Building & Running

### Docker (Recommended)

```bash
# Build the image
docker build -t merge-conflict-env:latest -f server/Dockerfile .

# Run the server
docker run --rm -p 8000:8000 merge-conflict-env:latest

# Health check
curl http://localhost:8000/health
```

### Without Docker

```bash
# Install dependencies
pip install -r server/requirements.txt

# Run the server
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Running Inference

```bash
# Set environment variables
export HF_TOKEN="your-token"
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4.1-mini"

# Run baseline inference
python inference.py
```

## Action Space

**MergeConflictAction** — controls interaction with the environment:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `action_type` | str | `"list_conflicts"` | Action to perform (see table below) |
| `file_path` | str | `""` | Target file path (for `view_file`, `resolve_file`) |
| `content` | str | `""` | Resolved content (for `resolve_file`) |

### Action Types

| Action | Description | Required Fields |
|--------|-------------|-----------------|
| `list_conflicts` | List all files with unresolved conflicts | — |
| `view_file` | View a file's content (with conflict markers) | `file_path` |
| `view_context` | View git log, branches, commit messages | — |
| `resolve_file` | Submit resolved content for a file | `file_path`, `content` |
| `run_tests` | Run pytest test suite to verify resolutions | — |
| `submit` | Finalize submission (ends episode) | — |

## Observation Space

**MergeConflictObservation** — returned after each action:

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether the action succeeded |
| `message` | str | Human-readable status message |
| `error` | str | Error message if action failed |
| `conflict_files` | list[str] | Files with unresolved conflicts |
| `file_content` | str | Content of requested file |
| `git_context` | str | Git log, branches, commit messages |
| `test_output` | str | Output from test suite |
| `resolution_status` | dict | Map of file -> resolved/unresolved |
| `conflicts_remaining` | int | Count of unresolved files |
| `task_id` | str | Current task identifier |
| `difficulty` | str | easy / medium / hard |
| `done` | bool | Whether episode is complete |
| `reward` | float | Reward for this step |

## Tasks

### Task 1: Simple Text Conflict (Easy)

- **Files**: 1 (README.md), **Conflicts**: 1 block
- Two developers edited the same README section
- `feature-install` added installation instructions
- `feature-setup` added a setup guide to the same section
- **Goal**: Combine both additions into a coherent document

### Task 2: Code Function Conflict (Medium)

- **Files**: 2 (utils.py, main.py), **Conflicts**: 3 blocks
- `refactor-types` renamed parameters and added type hints
- `feature-search` added a new search function using the old API
- **Goal**: Apply type refactoring AND integrate the new feature

### Task 3: Multi-File Refactor Conflict (Hard)

- **Files**: 4 (config.py, models.py, utils.py, api.py), **Conflicts**: 5-6 blocks
- `refactor-structure` converted to dataclasses, added config object, ID generation
- `feature-api` added Comment model, validation, rate limiting
- **Goal**: Merge structural refactoring with new features across all files

## Reward Function

The reward function provides **incremental, per-step feedback**:

| Component | Max Reward | How |
|-----------|-----------|-----|
| Conflict markers removed | +0.09 | No `<<<<<<<`, `=======`, `>>>>>>>` remaining |
| Syntax validity | +0.09 | Parseable Python (for .py files) |
| Content similarity | +0.55 | `difflib.SequenceMatcher` ratio vs gold resolution |
| Test pass rate | +0.09 | Proportion of pytest tests passing |
| Exploration | +0.02 | Per `list_conflicts`, `view_file`, `view_context` |

**Penalties**: −0.04 per step after step 15 (prevents loops). All rewards clamped to **(0.01, 0.99)**.

## Baseline Performance

The inference script ships with two agents:

1. **Deterministic agent** — always active. No LLM required. Views each conflicted file, merges both sides of every conflict block, submits. Establishes a reproducible floor score.
2. **LLM agent** (GPT-4.1-mini by default) — layered on top for higher quality resolutions.

| Task | Difficulty | Deterministic Score | GPT-4.1-mini Score | Steps |
|------|-----------|--------------------|--------------------|-------|
| easy_simple_text | Easy | ~0.55 | ~0.75 | 5-7 |
| medium_code_logic | Medium | ~0.35 | ~0.60 | 8-12 |
| hard_multi_file | Hard | ~0.25 | ~0.45 | 12-20 |

*Scores are approximate and depend on model and environment configuration.*

## Project Structure

```
merge_conflict_env/
├── __init__.py                        # Module exports
├── models.py                          # Action, Observation, State models
├── client.py                          # MergeConflictEnv HTTP/WS client
├── grader.py                          # Reward scoring logic
├── task_generator.py                  # Programmatic scenario generator
├── openenv.yaml                       # OpenEnv manifest
├── pyproject.toml                     # Dependencies
├── inference.py                       # Baseline LLM inference script
├── README.md                          # This file
├── tasks/                             # Pre-built conflict scenarios
│   ├── conftest.py                    # Shared pytest fixtures
│   ├── easy_simple_text/
│   │   ├── setup.py                   # Repo creation script
│   │   ├── gold_resolution/           # Expected correct files
│   │   └── tests/                     # Verification tests
│   ├── medium_code_logic/
│   │   ├── setup.py
│   │   ├── gold_resolution/
│   │   └── tests/
│   └── hard_multi_file/
│       ├── setup.py
│       ├── gold_resolution/
│       └── tests/
└── server/
    ├── __init__.py
    ├── merge_conflict_environment.py  # Core environment logic
    ├── app.py                         # FastAPI application
    ├── requirements.txt               # Server dependencies
    └── Dockerfile                     # Container image
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://api.openai.com/v1` | LLM API endpoint |
| `MODEL_NAME` | `gpt-4.1-mini` | Model identifier |
| `HF_TOKEN` | *(required)* | Hugging Face API token |
| `ENV_BASE_URL` | `http://localhost:8000` | Environment server URL |
| `WORKSPACE_DIR` | `/workspace` | Directory for task workspaces |
| `MAX_CONCURRENT_ENVS` | `8` | Max simultaneous sessions |
| `ENABLE_WEB_INTERFACE` | `true` | Serve a web UI at `/web` |

## Extending with New Tasks

Use `task_generator.py` to create custom conflict scenarios:

```python
from task_generator import ConflictScenario, BranchSpec, generate_conflict_repo

scenario = ConflictScenario(
    task_id="my_custom_task",
    difficulty="medium",
    description="Custom conflict scenario",
    base_files={"app.py": "base content..."},
    branch_a=BranchSpec(
        name="branch-a",
        commit_message="Change A",
        files={"app.py": "branch A content..."},
    ),
    branch_b=BranchSpec(
        name="branch-b",
        commit_message="Change B",
        files={"app.py": "branch B content..."},
    ),
    gold_resolutions={"app.py": "merged content..."},
)

generate_conflict_repo(scenario, "/tmp/my_task")
```
