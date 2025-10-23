"""Utilities for retrieving daily news articles."""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import List, Sequence

try:  # pragma: no cover - allow importing without optional dependency installed
    import requests
    from requests import RequestException
except ImportError as exc:  # pragma: no cover - dependency validated at runtime
    requests = None  # type: ignore[assignment]
    RequestException = Exception  # type: ignore[assignment,misc]
    _REQUESTS_IMPORT_ERROR = (
        "The 'requests' package is required to fetch news. Install it with 'pip install requests'"
        f" (original error: {exc})."
    )
else:
    _REQUESTS_IMPORT_ERROR = None

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """Structured representation of a news article."""

    keyword: str
    title: str
    description: str
    url: str
    source: str
    published_at: dt.datetime
    content: str | None = None

    @property
    def canonical_title(self) -> str:
        return " ".join(self.title.lower().split())


class NewsFetcher:
    """Fetches news articles for a collection of keywords using NewsAPI."""

    def __init__(self, config: Config):
        if not config.news_api_key:
            raise RuntimeError(
                "NEWS_API_KEY is not configured."
                " Sign up at https://newsapi.org to obtain an API key and set it"
                " in your environment before running the crawler."
            )
        self._config = config

    def fetch(self, keywords: Sequence[str], target_date: dt.date | None = None) -> List[Article]:
        """Fetch deduplicated articles for a set of keywords."""

        seen_urls: set[str] = set()
        collected: List[Article] = []
        target_date = target_date or dt.datetime.utcnow().date()

        for keyword in keywords:
            logger.info("Fetching news for keyword '%s'", keyword)
            try:
                articles = self._fetch_keyword(keyword, target_date)
            except RuntimeError as exc:
                logger.error("Skipping keyword '%s' due to fetch error: %s", keyword, exc)
                continue
            for article in articles:
                if article.url in seen_urls:
                    continue
                seen_urls.add(article.url)
                collected.append(article)

        return collected

    def _fetch_keyword(self, keyword: str, target_date: dt.date) -> List[Article]:
        if requests is None:  # pragma: no cover - dependency guard
            raise RuntimeError(str(_REQUESTS_IMPORT_ERROR))
        params = self._build_params(keyword, target_date)
        try:
            response = requests.get(
                self._config.news_api_endpoint,
                params=params,
                headers={"X-Api-Key": self._config.news_api_key},
                timeout=self._config.request_timeout,
            )
            response.raise_for_status()
        except RequestException as exc:
            raise RuntimeError(f"Failed to fetch news from NewsAPI: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("NewsAPI returned a non-JSON response.") from exc

        articles = []
        for item in payload.get("articles", [])[: self._config.max_articles_per_keyword]:
            articles.append(self._build_article(keyword, item))
        return articles

    def _build_params(self, keyword: str, target_date: dt.date) -> dict[str, str]:
        start = dt.datetime.combine(target_date, dt.time.min)
        end = dt.datetime.combine(target_date, dt.time.max)
        return {
            "q": keyword,
            "from": start.isoformat(timespec="seconds"),
            "to": end.isoformat(timespec="seconds"),
            "language": self._config.news_language,
            "sortBy": "relevancy",
            "pageSize": str(self._config.max_articles_per_keyword),
        }

    @staticmethod
    def _build_article(keyword: str, item: dict) -> Article:
        published_raw = item.get("publishedAt")
        published_at = _parse_timestamp(published_raw) if published_raw else dt.datetime.utcnow()
        source = (item.get("source") or {}).get("name", "Unknown source")
        return Article(
            keyword=keyword,
            title=item.get("title") or "Untitled",
            description=item.get("description") or "",
            url=item.get("url") or "",
            source=source,
            published_at=published_at,
            content=item.get("content"),
        )


def _parse_timestamp(raw: str) -> dt.datetime:
    if raw.endswith("Z"):
        raw = raw.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(raw)
    except ValueError:
        logger.warning("Failed to parse timestamp '%s', defaulting to UTC now", raw)
        return dt.datetime.utcnow()


__all__ = ["Article", "NewsFetcher"]
