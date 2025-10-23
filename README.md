# AI-Crawler

Daily AI-assisted news crawler tailored for private-banking researchers. Provide one or
more keywords and the tool pulls in the day's coverage, groups duplicate stories, and
uses OpenAI's GPT models to highlight the takeaways that matter for wealth-management
and market-focused teams.

## Features

- 🔎 Fetches articles for each keyword from [NewsAPI](https://newsapi.org) filtered to the
  current day.
- 🧠 Uses OpenAI GPT models (defaults to `gpt-3.1-mini`, configurable to other
  available models) to summarise and extract
  private-banking-relevant key points.
- ♻️ Clusters duplicate headlines so the summary reflects the overall story rather than
  repeated links.
- 📝 Generates an easy-to-read Markdown briefing that can be saved or piped into your own
  workflows.

## Prerequisites

- Python 3.10 or newer.
- An OpenAI API key with access to GPT models (place it in `OPENAI_API_KEY`).
- A [NewsAPI](https://newsapi.org) key for sourcing the latest headlines (`NEWS_API_KEY`).
- Optional: a `.env` file for configuration (start from `.env.example`).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\\Scripts\\activate`
pip install -e .
cp .env.example .env  # then edit .env with your keys
```

### Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | **Required.** OpenAI secret key. | — |
| `OPENAI_MODEL` | GPT model used for summarisation (e.g. `gpt-3.1-mini`). | `gpt-3.1-mini` |
| `NEWS_API_KEY` | **Required.** NewsAPI key. | — |
| `NEWS_API_ENDPOINT` | Alternative endpoint if you self-host a compatible API. | `https://newsapi.org/v2/everything` |
| `NEWS_LANGUAGE` | Restrict results to a specific language. | `en` |
| `MAX_ARTICLES_PER_KEYWORD` | Limit fetched articles per keyword before clustering. | `15` |
| `REQUEST_TIMEOUT` | HTTP timeout for NewsAPI requests (seconds). | `30` |

## Usage

Run the CLI with one or more keywords:

```bash
ai-crawler AI "private banking" fintech
```

Or load keywords from a file:

```bash
ai-crawler --keywords-file keywords.txt
```

Specify a date (UTC) and write the report to disk:

```bash
ai-crawler AI --date 2024-05-01 --output briefings/2024-05-01.md
```

The command prints (or writes) a Markdown report similar to:

```markdown
# Daily AI News Briefing — 2024-05-01

## Keyword: AI
### Topic 1
Concise overview of the development.

**Key Points**
- Why the story matters for private banking clients.
- Portfolio or risk management implications.

**Headlines**
- Major bank launches new AI wealth product — Financial Times
- Major bank launches new AI wealth product — Reuters

**Sources**
- https://www.ft.com/... 
- https://www.reuters.com/...
```

## Development notes

- Clustering relies on fuzzy matching of article titles. Adjust `similarity_threshold`
  in `ai_crawler/aggregator.py` if you need stricter or looser grouping.
- The summariser uses the OpenAI Responses API and requests structured JSON output. If
  you prefer a different model (for example, GPT-3.5, GPT-4, or a fine-tuned variant),
  update `OPENAI_MODEL` in your environment.
- Error handling falls back to headline lists when the LLM cannot be reached, ensuring
  the run still produces useful output.
- Run the automated checks locally with `pytest` before committing changes.
