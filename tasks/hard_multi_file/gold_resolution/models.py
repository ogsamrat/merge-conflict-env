"""Data models with type annotations."""

from dataclasses import dataclass
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


@dataclass
class Comment:
    text: str
    author: str
    item_title: str
    comment_id: Optional[str] = None

    def to_dict(self) -> dict:
        result = {
            "text": self.text,
            "author": self.author,
            "item_title": self.item_title,
        }
        if self.comment_id:
            result["comment_id"] = self.comment_id
        return result
