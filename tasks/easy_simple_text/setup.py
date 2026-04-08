"""
Easy Task: Simple Text Conflict

Creates a git repo with a merge conflict in a single README.md file.
- Branch 'feature-install': Adds installation instructions
- Branch 'feature-setup': Rewrites the same section with setup guide
- Merging them produces a single conflict block.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

BASE_README = """\
# MyProject

A simple utility library for data processing.

## Getting Started

To get started with MyProject, clone the repository and follow the instructions below.

## Usage

```python
from myproject import process
result = process(data)
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

MIT License
"""

BRANCH_A_README = """\
# MyProject

A simple utility library for data processing.

## Getting Started

To get started with MyProject, clone the repository and follow the instructions below.

## Installation

To install MyProject, run the following commands:

```bash
pip install myproject
```

Or install from source:

```bash
git clone https://github.com/example/myproject.git
cd myproject
pip install -e .
```

### Requirements

- Python 3.9 or higher
- pip 21.0 or higher

## Usage

```python
from myproject import process
result = process(data)
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

MIT License
"""

BRANCH_B_README = """\
# MyProject

A simple utility library for data processing.

## Getting Started

To get started with MyProject, clone the repository and follow the instructions below.

## Setup Guide

Follow these steps to set up your development environment:

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the test suite: `pytest`

### Environment Variables

Set the following environment variables before running:

- `MYPROJECT_ENV`: Set to `development` or `production`
- `MYPROJECT_DEBUG`: Set to `true` to enable debug logging

## Usage

```python
from myproject import process
result = process(data)
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

MIT License
"""


def setup_task(workspace_dir: str) -> None:
    """Create the conflicted git repo in workspace_dir."""
    ws = Path(workspace_dir)
    ws.mkdir(parents=True, exist_ok=True)

    def run_git(*args: str) -> None:
        subprocess.run(
            ["git"] + list(args),
            cwd=str(ws),
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "Dev", "GIT_AUTHOR_EMAIL": "dev@test.com",
                 "GIT_COMMITTER_NAME": "Dev", "GIT_COMMITTER_EMAIL": "dev@test.com"},
        )

    run_git("init")
    run_git("checkout", "-b", "main")

    (ws / "README.md").write_text(BASE_README, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Initial commit: add README.md")

    run_git("checkout", "-b", "feature-install")
    (ws / "README.md").write_text(BRANCH_A_README, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Add installation instructions to README")

    run_git("checkout", "main")
    run_git("checkout", "-b", "feature-setup")
    (ws / "README.md").write_text(BRANCH_B_README, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Add setup guide with environment variables to README")

    run_git("checkout", "feature-install")
    try:
        subprocess.run(
            ["git", "merge", "feature-setup", "--no-edit"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "Dev", "GIT_AUTHOR_EMAIL": "dev@test.com",
                 "GIT_COMMITTER_NAME": "Dev", "GIT_COMMITTER_EMAIL": "dev@test.com"},
        )
    except subprocess.CalledProcessError:
        pass


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        setup_task(tmp)
        readme = Path(tmp) / "README.md"
        print(readme.read_text(encoding="utf-8"))
