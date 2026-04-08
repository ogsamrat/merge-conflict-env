"""Application configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    database_url: str = "sqlite:///app.db"
    debug: bool = False
    secret_key: str = "change-me"
    max_items: int = 100
    api_version: str = "v1"
    rate_limit: int = 60
    allowed_origins: tuple = ("http://localhost:3000",)


config = AppConfig()
