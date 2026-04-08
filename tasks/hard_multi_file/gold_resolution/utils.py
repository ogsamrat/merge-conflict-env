"""Utility helpers with type annotations."""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def sanitize_string(text: str) -> str:
    """Remove leading/trailing whitespace and normalize."""
    return text.strip().lower()


def generate_id(prefix: str = "") -> str:
    """Generate a simple unique identifier."""
    import uuid
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}{uid}" if prefix else uid


def validate_length(text: str, max_length: int = 500) -> bool:
    """Validate that text does not exceed max length."""
    return len(text.strip()) <= max_length
