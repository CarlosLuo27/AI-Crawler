"""Command line interface for the AI-powered news crawler."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Iterable, List

try:  # Optional dependency for .env loading
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional enhancement
    load_dotenv = None  # type: ignore

from .config import Config


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarise today's news using GPT.")
    parser.add_argument(
        "keywords",
        nargs="*",
        help="Keywords to search for (provide multiple to broaden coverage).",
    )
    parser.add_argument(
        "--keywords-file",
        type=Path,
        help="Optional file containing newline-separated keywords.",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="ISO date (YYYY-MM-DD) to fetch news for; defaults to today in UTC.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the markdown summary to this file instead of stdout.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def resolve_keywords(args: argparse.Namespace) -> List[str]:
    keywords: List[str] = []
    if args.keywords:
        for keyword in args.keywords:
            keyword = keyword.strip()
            if keyword:
                keywords.append(keyword)
    if args.keywords_file:
        contents = args.keywords_file.read_text(encoding="utf-8")
        for line in contents.splitlines():
            line = line.strip()
            if line:
                keywords.append(line)
    deduped = sorted(set(keywords))
    if not deduped:
        raise SystemExit("No keywords provided. Supply them via CLI or --keywords-file.")
    return deduped


def parse_date(raw: str | None) -> dt.date | None:
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - user input guard
        raise SystemExit(f"Invalid --date value '{raw}': {exc}") from exc


def format_markdown(briefing) -> str:
    lines: List[str] = []
    lines.append(f"# Daily AI News Briefing — {briefing.date.isoformat()}")
    lines.append("")
    if not briefing.briefings:
        lines.append("No relevant articles were found for the provided keywords.")
        return "\n".join(lines)

    for keyword_briefing in briefing.briefings:
        lines.append(f"## Keyword: {keyword_briefing.keyword}")
        if not keyword_briefing.summaries:
            lines.append("No coverage detected for this keyword.")
            lines.append("")
            continue
        for idx, summary in enumerate(keyword_briefing.summaries, start=1):
            lines.append(f"### Topic {idx}")
            lines.append(summary.topic_summary.strip() or "(No summary generated)")
            if summary.key_points:
                lines.append("")
                lines.append("**Key Points**")
                for point in summary.key_points:
                    lines.append(f"- {point}")
            if summary.headlines:
                lines.append("")
                lines.append("**Headlines**")
                for headline in summary.headlines:
                    lines.append(f"- {headline}")
            if summary.sources:
                lines.append("")
                lines.append("**Sources**")
                for source in summary.sources:
                    lines.append(f"- {source}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    if load_dotenv is not None:
        load_dotenv()
    args = parse_args(argv)
    keywords = resolve_keywords(args)
    target_date = parse_date(args.date)

    config = Config.from_env()
    from .pipeline import Pipeline  # Local import avoids requiring OpenAI for helper tests
    pipeline = Pipeline(config)
    briefing = pipeline.run(keywords, target_date)
    output = format_markdown(briefing)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
