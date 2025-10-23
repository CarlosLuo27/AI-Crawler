"""Configuration helpers for the AI crawler."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration values sourced from the environment."""

    openai_api_key: str
    openai_model: str = "gpt-3.1-mini"
    news_api_key: Optional[str] = None
    news_api_endpoint: str = "https://newsapi.org/v2/everything"
    news_language: str = "en"
    max_articles_per_keyword: int = 15
    request_timeout: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config: Configured dataclass.

        Raises:
            RuntimeError: If a required environment variable is missing.
        """

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise RuntimeError(
                "Missing required OPENAI_API_KEY environment variable."
                " Set it in your shell or an .env file before running the app."
            )

        return cls(
            openai_api_key=openai_api_key,
            openai_model=os.getenv("OPENAI_MODEL", cls.openai_model),
            news_api_key=os.getenv("NEWS_API_KEY"),
            news_api_endpoint=os.getenv("NEWS_API_ENDPOINT", cls.news_api_endpoint),
            news_language=os.getenv("NEWS_LANGUAGE", cls.news_language),
            max_articles_per_keyword=int(
                os.getenv("MAX_ARTICLES_PER_KEYWORD", cls.max_articles_per_keyword)
            ),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", cls.request_timeout)),
        )


__all__ = ["Config"]
