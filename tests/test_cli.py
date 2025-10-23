import datetime as dt
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from ai_crawler.cli import format_markdown, parse_date, resolve_keywords


@dataclass
class _GroupSummary:
    keyword: str
    topic_summary: str
    key_points: list[str]
    headlines: list[str]
    sources: list[str]


@dataclass
class _KeywordBriefing:
    keyword: str
    summaries: list[_GroupSummary]


@dataclass
class _DailyBriefing:
    date: dt.date
    briefings: list[_KeywordBriefing]


def test_resolve_keywords_merges_cli_and_file(tmp_path):
    keywords_file = tmp_path / "keywords.txt"
    keywords_file.write_text("AI\nwealth\nAI\n", encoding="utf-8")

    args = SimpleNamespace(keywords=["AI", "Fintech"], keywords_file=keywords_file)
    assert resolve_keywords(args) == ["AI", "Fintech", "wealth"]


def test_resolve_keywords_requires_input():
    args = SimpleNamespace(keywords=[], keywords_file=None)
    with pytest.raises(SystemExit):
        resolve_keywords(args)


def test_parse_date_handles_none_and_valid_values():
    assert parse_date(None) is None
    assert parse_date("2024-05-01") == dt.date(2024, 5, 1)


def test_parse_date_rejects_invalid_input():
    with pytest.raises(SystemExit):
        parse_date("2024-13-01")


def test_format_markdown_outputs_sections():
    summary = _GroupSummary(
        keyword="AI",
        topic_summary="Summary body",
        key_points=["Point 1"],
        headlines=["Headline — Source"],
        sources=["https://example.com"],
    )
    briefing = _DailyBriefing(
        date=dt.date(2024, 5, 1),
        briefings=[_KeywordBriefing(keyword="AI", summaries=[summary])],
    )

    output = format_markdown(briefing)
    assert output.endswith("\n")
    assert "# Daily AI News Briefing — 2024-05-01" in output
    assert "## Keyword: AI" in output
    assert "**Key Points**" in output
    assert "- Point 1" in output
    assert "- https://example.com" in output


def test_format_markdown_handles_missing_articles():
    briefing = _DailyBriefing(date=dt.date(2024, 5, 1), briefings=[])
    output = format_markdown(briefing)
    assert "No relevant articles" in output
