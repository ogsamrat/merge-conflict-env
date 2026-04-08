"""API endpoint handlers with typed config."""

from models import User, Item, Comment
from utils import validate_email, sanitize_string, generate_id, validate_length
from config import config


def create_user(name: str, email: str) -> dict:
    """Create a new user with generated ID."""
    if not validate_email(email):
        return {"error": "Invalid email"}
    clean_name = sanitize_string(name)
    user = User(name=clean_name, email=email, user_id=generate_id("user-"))
    return user.to_dict()


def create_item(title: str, description: str, owner: str) -> dict:
    """Create a new item with generated ID and validation."""
    if not validate_length(description):
        return {"error": "Description too long"}
    item = Item(
        title=sanitize_string(title),
        description=description,
        owner=owner,
        item_id=generate_id("item-"),
    )
    return item.to_dict()


def create_comment(text: str, author: str, item_title: str) -> dict:
    """Create a comment on an item with generated ID."""
    if not validate_length(text, max_length=200):
        return {"error": "Comment too long"}
    comment = Comment(
        text=sanitize_string(text),
        author=author,
        item_title=item_title,
        comment_id=generate_id("comment-"),
    )
    return comment.to_dict()


def list_items(items: list) -> list:
    """List all items up to max configured limit."""
    return [item.to_dict() for item in items[:config.max_items]]
