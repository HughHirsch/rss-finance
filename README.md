# rss-finance

A local pipeline that collects financial-news RSS feeds into SQLite, indexes the
articles with a local embedding model, and answers questions about them with a
local LLM served by Ollama (RAG). Built for personal use.

## Layout

```
rss-finance/
├── collector/      # fetch feeds on a schedule → data/articles.db   (feedparser, SQLite)
├── model/          # index + RAG over the articles, later extraction (LanceDB, Ollama)
├── data/           # gitignored: articles.db, logs
├── docs/           # guides, starting with docs/COLLECTOR.md
└── pyproject.toml  # uv workspace tying the two packages together
```

The collector and the model are separate Python packages in one uv workspace. Each has its
own dependencies, so the collector can run on its own (for example on an always-on box)
without LanceDB or Ollama. The only contract between them is the SQLite schema the collector
writes and `model/src/rss_finance_model/articles.py` reads.

## Getting started

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # uv, if not installed
cd ~/GitHub/rss-finance
uv sync --all-packages                            # Python 3.12 + both packages
```

- Collector: [docs/COLLECTOR.md](docs/COLLECTOR.md), then work in `collector/`.
- Model: [model/README.md](model/README.md) and [model/docs/TUTORIAL.md](model/docs/TUTORIAL.md).

Run checks from inside each package folder: `uv run pytest`, `uv run ruff check .`,
`uv run mypy src`.
