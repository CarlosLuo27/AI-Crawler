"""High level orchestration for the AI news crawler."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Sequence

from .aggregator import cluster_articles
from .config import Config
from .news import Article, NewsFetcher
from .summarizer import GroupSummary, Summarizer


@dataclass
class KeywordBriefing:
    keyword: str
    summaries: List[GroupSummary]


@dataclass
class DailyBriefing:
    date: dt.date
    briefings: List[KeywordBriefing]


class Pipeline:
    """Coordinates fetching, clustering and summarisation."""

    def __init__(self, config: Config):
        self._config = config
        self._fetcher = NewsFetcher(config)
        self._summarizer = Summarizer(config)

    def run(self, keywords: Sequence[str], target_date: dt.date | None = None) -> DailyBriefing:
        target_date = target_date or dt.datetime.utcnow().date()
        articles = self._fetcher.fetch(keywords, target_date)
        grouped = self._group_by_keyword(articles)

        briefings: List[KeywordBriefing] = []
        for keyword, keyword_articles in grouped.items():
            clusters = cluster_articles(keyword_articles)
            summaries: List[GroupSummary] = []
            for cluster in clusters:
                summaries.append(self._summarise_cluster(keyword, cluster))
            briefings.append(KeywordBriefing(keyword=keyword, summaries=summaries))

        return DailyBriefing(date=target_date, briefings=briefings)

    def _group_by_keyword(self, articles: Sequence[Article]) -> Dict[str, List[Article]]:
        grouped: Dict[str, List[Article]] = {}
        for article in articles:
            grouped.setdefault(article.keyword, []).append(article)
        return grouped

    def _summarise_cluster(self, keyword: str, cluster: Sequence[Article]) -> GroupSummary:
        try:
            return self._summarizer.summarise_group(keyword, cluster)
        except Exception as exc:  # pragma: no cover - defensive fallback
            fallback_headlines = [f"{article.title} — {article.source}" for article in cluster]
            fallback_sources = [article.url for article in cluster if article.url]
            return GroupSummary(
                keyword=keyword,
                topic_summary=(
                    "Automatic summarisation failed; review the gathered headlines manually."
                    f" Error: {exc}"
                ),
                key_points=fallback_headlines,
                headlines=fallback_headlines,
                sources=fallback_sources,
            )


__all__ = ["DailyBriefing", "KeywordBriefing", "Pipeline"]
