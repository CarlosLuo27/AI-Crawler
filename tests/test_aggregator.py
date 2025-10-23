import datetime as dt

from ai_crawler.aggregator import cluster_articles
from ai_crawler.news import Article


def make_article(title: str, url: str, published_at: dt.datetime | None = None) -> Article:
    return Article(
        keyword="AI",
        title=title,
        description="",
        url=url,
        source="Test Source",
        published_at=published_at or dt.datetime.utcnow(),
        content=None,
    )


def test_cluster_articles_groups_similar_titles():
    articles = [
        make_article("Bank launches new AI wealth tool", "1"),
        make_article("Bank debuts new AI wealth tool", "2"),
        make_article("Private bank expands family office team", "3"),
    ]

    clusters = cluster_articles(articles, similarity_threshold=0.7)
    sizes = sorted(len(cluster) for cluster in clusters)

    assert sizes == [1, 2]
