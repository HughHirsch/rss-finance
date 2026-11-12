# rss-finance

A local pipeline that collects financial-news RSS feeds into SQLite, indexes the
articles with a local embedding model, and answers questions about them with a
local LLM served by Ollama (RAG). Built for personal use.

## Layout

```
rss-finance/
├── model/          # index + RAG over the articles, later extraction (LanceDB, Ollama)
├── feeds.toml      # the feed list the collector reads (run it from this folder)
├── local.toml      # gitignored: contact for the collector's User-Agent
├── data/           # gitignored: articles.db, logs
└── pyproject.toml  # uv project: the model workspace member plus the collector dependency
```

The collector lives in its own repo, [rss-collector](https://github.com/HughHirsch/rss-collector),
and is installed from git. The model is a package in this repo. The only contract between
them is the SQLite schema the collector writes and `model/src/rss_finance_model/articles.py`
reads.

## Getting started

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # uv, if not installed
cd ~/GitHub/rss-finance
uv sync --all-packages                            # Python 3.12 + model + collector
uv run rss-finance-collector collect              # one pass over feeds.toml
```

- Collector: work in the [rss-collector](https://github.com/HughHirsch/rss-collector) repo
  (its guide is `docs/COLLECTOR.md` there).
- Model: [model/README.md](model/README.md) and [model/docs/TUTORIAL.md](model/docs/TUTORIAL.md).

Run the model's checks from `model/`: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.
