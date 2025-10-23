"""LLM-powered summarisation utilities."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from openai import OpenAI
from openai import OpenAIError

from .config import Config
from .news import Article


logger = logging.getLogger(__name__)


@dataclass
class GroupSummary:
    """Summary describing a cluster of related articles."""

    keyword: str
    topic_summary: str
    key_points: List[str]
    headlines: List[str]
    sources: List[str]


class Summarizer:
    """Wraps the OpenAI client to summarise news article clusters."""

    def __init__(self, config: Config):
        self._client = OpenAI(api_key=config.openai_api_key)
        self._model = config.openai_model

    def summarise_group(self, keyword: str, articles: Sequence[Article]) -> GroupSummary:
        """Summarise a group of related articles."""

        prompt = self._build_prompt(keyword, articles)
        try:
            response = self._client.responses.create(
                model=self._model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are an analyst helping a private-banking research team"
                            " understand today's developments."
                            " Craft concise, insight-focused summaries."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                response_format={"type": "json_object"},
            )
        except OpenAIError as exc:  # pragma: no cover - network interaction
            logger.error("OpenAI request failed: %s", exc)
            raise

        payload = self._extract_response_text(response)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode JSON payload returned by OpenAI: %s", payload)
            raise ValueError("OpenAI returned malformed JSON.") from exc
        return GroupSummary(
            keyword=keyword,
            topic_summary=data.get("topic_summary", ""),
            key_points=[point.strip() for point in data.get("key_points", []) if point],
            headlines=[headline.strip() for headline in data.get("headlines", []) if headline],
            sources=[src for src in data.get("sources", []) if src],
        )

    @staticmethod
    def _build_prompt(keyword: str, articles: Sequence[Article]) -> str:
        article_blocks = []
        for article in articles:
            block = (
                f"Title: {article.title}\n"
                f"Source: {article.source}\n"
                f"Published: {article.published_at.isoformat()}\n"
                f"URL: {article.url}\n"
                f"Description: {article.description or 'N/A'}"
            )
            article_blocks.append(block)

        article_section = "\n---\n".join(article_blocks)
        return (
            "Summarise the following news articles that relate to today's keyword"
            f" '{keyword}'. Grouped articles often cover the same development;"
            " integrate them into a single coherent update."
            "\n\nArticles:\n"
            f"{article_section}"
            "\n\nReturn a JSON object with the keys:"
            "\n- topic_summary: 3-4 sentence overview of the combined development."
            "\n- key_points: list of 3-5 bullet points highlighting why the news matters"
            " for private banking, wealth management or markets."
            "\n- headlines: list capturing each headline with its source."
            "\n- sources: list of URLs for citation."
        )

    @staticmethod
    def _extract_response_text(response) -> str:
        """Best-effort extraction of text content from a Responses API result."""

        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text
        if isinstance(output_text, Iterable):
            combined = "".join(str(part) for part in output_text).strip()
            if combined:
                return combined

        output = getattr(response, "output", None)
        if output:
            fragments: List[str] = []
            for item in output:
                content = getattr(item, "content", [])
                for element in content:
                    text = getattr(element, "text", None)
                    if text is None:
                        continue
                    value = getattr(text, "value", text)
                    if value:
                        fragments.append(str(value))
            combined = "".join(fragments).strip()
            if combined:
                return combined

        raise ValueError("OpenAI response did not contain any text payload.")


__all__ = ["GroupSummary", "Summarizer"]
