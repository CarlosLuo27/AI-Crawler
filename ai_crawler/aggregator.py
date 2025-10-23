"""Grouping and deduplication helpers for news articles."""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable, List, Sequence

from .news import Article


def cluster_articles(
    articles: Sequence[Article], *, similarity_threshold: float = 0.75
) -> List[List[Article]]:
    """Group articles that likely cover the same topic based on title similarity."""

    clusters: List[List[Article]] = []

    for article in sorted(articles, key=lambda a: a.published_at, reverse=True):
        placed = False
        for cluster in clusters:
            if _is_similar(article, cluster, similarity_threshold):
                cluster.append(article)
                placed = True
                break
        if not placed:
            clusters.append([article])

    return clusters


def _is_similar(article: Article, cluster: Iterable[Article], threshold: float) -> bool:
    for existing in cluster:
        ratio = SequenceMatcher(None, article.canonical_title, existing.canonical_title).ratio()
        if ratio >= threshold:
            return True
    return False


__all__ = ["cluster_articles"]
