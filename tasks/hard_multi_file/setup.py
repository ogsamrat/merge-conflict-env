"""
Hard Task: Multi-File Refactor Conflict

Creates a git repo with merge conflicts across 4 Python files.
- Branch 'refactor-structure': Restructures project, adds type hints, splits config
- Branch 'feature-api': Adds new API endpoints and validation logic
- Merging produces 5-6 conflict blocks across models.py, api.py, utils.py, config.py
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# ── Base versions ──

BASE_CONFIG = '''\
"""Application configuration."""

DATABASE_URL = "sqlite:///app.db"
DEBUG = False
SECRET_KEY = "change-me"
MAX_ITEMS = 100
'''

BASE_MODELS = '''\
"""Data models."""


class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def to_dict(self):
        return {"name": self.name, "email": self.email}


class Item:
    def __init__(self, title, description, owner):
        self.title = title
        self.description = description
        self.owner = owner

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
        }
'''

BASE_UTILS = '''\
"""Utility helpers."""


def validate_email(email):
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[1]


def sanitize_string(text):
    """Remove leading/trailing whitespace and normalize."""
    return text.strip().lower()
'''

BASE_API = '''\
"""API endpoint handlers."""

from models import User, Item
from utils import validate_email, sanitize_string
from config import MAX_ITEMS


def create_user(name, email):
    """Create a new user."""
    if not validate_email(email):
        return {"error": "Invalid email"}
    clean_name = sanitize_string(name)
    user = User(clean_name, email)
    return user.to_dict()


def create_item(title, description, owner):
    """Create a new item."""
    item = Item(
        sanitize_string(title),
        description,
        owner,
    )
    return item.to_dict()


def list_items(items):
    """List all items up to MAX_ITEMS."""
    return [item.to_dict() for item in items[:MAX_ITEMS]]
'''

# ── Branch A: refactor-structure ──

BRANCH_A_CONFIG = '''\
"""Application configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    database_url: str = "sqlite:///app.db"
    debug: bool = False
    secret_key: str = "change-me"
    max_items: int = 100
    api_version: str = "v1"


config = AppConfig()
'''

BRANCH_A_MODELS = '''\
"""Data models with type annotations."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    name: str
    email: str
    user_id: Optional[str] = None

    def to_dict(self) -> dict:
        result = {"name": self.name, "email": self.email}
        if self.user_id:
            result["user_id"] = self.user_id
        return result


@dataclass
class Item:
    title: str
    description: str
    owner: str
    item_id: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
        }
        if self.item_id:
            result["item_id"] = self.item_id
        return result
'''

BRANCH_A_UTILS = '''\
"""Utility helpers with type annotations."""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def sanitize_string(text: str) -> str:
    """Remove leading/trailing whitespace and normalize."""
    return text.strip().lower()


def generate_id(prefix: str = "") -> str:
    """Generate a simple unique identifier."""
    import uuid
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}{uid}" if prefix else uid
'''

BRANCH_A_API = '''\
"""API endpoint handlers with typed config."""

from models import User, Item
from utils import validate_email, sanitize_string, generate_id
from config import config


def create_user(name: str, email: str) -> dict:
    """Create a new user with generated ID."""
    if not validate_email(email):
        return {"error": "Invalid email"}
    clean_name = sanitize_string(name)
    user = User(name=clean_name, email=email, user_id=generate_id("user-"))
    return user.to_dict()


def create_item(title: str, description: str, owner: str) -> dict:
    """Create a new item with generated ID."""
    item = Item(
        title=sanitize_string(title),
        description=description,
        owner=owner,
        item_id=generate_id("item-"),
    )
    return item.to_dict()


def list_items(items: list) -> list:
    """List all items up to max configured limit."""
    return [item.to_dict() for item in items[:config.max_items]]
'''

# ── Branch B: feature-api ──

BRANCH_B_CONFIG = '''\
"""Application configuration."""

DATABASE_URL = "sqlite:///app.db"
DEBUG = False
SECRET_KEY = "change-me"
MAX_ITEMS = 100
RATE_LIMIT = 60
ALLOWED_ORIGINS = ["http://localhost:3000"]
'''

BRANCH_B_MODELS = '''\
"""Data models."""


class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def to_dict(self):
        return {"name": self.name, "email": self.email}


class Item:
    def __init__(self, title, description, owner):
        self.title = title
        self.description = description
        self.owner = owner

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
        }


class Comment:
    def __init__(self, text, author, item_title):
        self.text = text
        self.author = author
        self.item_title = item_title

    def to_dict(self):
        return {
            "text": self.text,
            "author": self.author,
            "item_title": self.item_title,
        }
'''

BRANCH_B_UTILS = '''\
"""Utility helpers."""


def validate_email(email):
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[1]


def sanitize_string(text):
    """Remove leading/trailing whitespace and normalize."""
    return text.strip().lower()


def validate_length(text, max_length=500):
    """Validate that text does not exceed max length."""
    return len(text.strip()) <= max_length
'''

BRANCH_B_API = '''\
"""API endpoint handlers."""

from models import User, Item, Comment
from utils import validate_email, sanitize_string, validate_length
from config import MAX_ITEMS, RATE_LIMIT


def create_user(name, email):
    """Create a new user."""
    if not validate_email(email):
        return {"error": "Invalid email"}
    clean_name = sanitize_string(name)
    user = User(clean_name, email)
    return user.to_dict()


def create_item(title, description, owner):
    """Create a new item with validation."""
    if not validate_length(description):
        return {"error": "Description too long"}
    item = Item(
        sanitize_string(title),
        description,
        owner,
    )
    return item.to_dict()


def create_comment(text, author, item_title):
    """Create a comment on an item."""
    if not validate_length(text, max_length=200):
        return {"error": "Comment too long"}
    comment = Comment(
        text=sanitize_string(text),
        author=author,
        item_title=item_title,
    )
    return comment.to_dict()


def list_items(items):
    """List all items up to MAX_ITEMS."""
    return [item.to_dict() for item in items[:MAX_ITEMS]]
'''


def setup_task(workspace_dir: str) -> None:
    """Create the conflicted git repo in workspace_dir."""
    ws = Path(workspace_dir)
    ws.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Dev",
        "GIT_AUTHOR_EMAIL": "dev@test.com",
        "GIT_COMMITTER_NAME": "Dev",
        "GIT_COMMITTER_EMAIL": "dev@test.com",
    }

    def run_git(*args: str) -> None:
        subprocess.run(
            ["git"] + list(args), cwd=str(ws),
            capture_output=True, text=True, check=True, env=env,
        )

    def write_files(config_c, models_c, utils_c, api_c):
        (ws / "config.py").write_text(config_c, encoding="utf-8")
        (ws / "models.py").write_text(models_c, encoding="utf-8")
        (ws / "utils.py").write_text(utils_c, encoding="utf-8")
        (ws / "api.py").write_text(api_c, encoding="utf-8")

    run_git("init")
    run_git("checkout", "-b", "main")
    write_files(BASE_CONFIG, BASE_MODELS, BASE_UTILS, BASE_API)
    run_git("add", ".")
    run_git("commit", "-m", "Initial commit: project with models, utils, api, config")

    run_git("checkout", "-b", "refactor-structure")
    write_files(BRANCH_A_CONFIG, BRANCH_A_MODELS, BRANCH_A_UTILS, BRANCH_A_API)
    run_git("add", ".")
    run_git("commit", "-m", "Refactor: dataclasses, type hints, config object, ID generation")

    run_git("checkout", "main")
    run_git("checkout", "-b", "feature-api")
    write_files(BRANCH_B_CONFIG, BRANCH_B_MODELS, BRANCH_B_UTILS, BRANCH_B_API)
    run_git("add", ".")
    run_git("commit", "-m", "Feature: add Comment model, validation, rate limiting, CORS config")

    run_git("checkout", "refactor-structure")
    subprocess.run(
        ["git", "merge", "feature-api", "--no-edit"],
        cwd=str(ws), capture_output=True, text=True, env=env,
    )


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        setup_task(tmp)
        for f in ["config.py", "models.py", "utils.py", "api.py"]:
            p = Path(tmp) / f
            if p.exists():
                print(f"\n=== {f} ===")
                print(p.read_text(encoding="utf-8"))
