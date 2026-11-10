# model

The model side of rss-finance: the vector index and RAG over the collected articles, then
entity and relationship extraction with a local LLM, and later fine-tuning. It reads the
SQLite database the [collector](../collector) writes to `data/articles.db` at the repo root.

Everything runs locally: embeddings and the chat model are served by Ollama on the GPU.

## Setup (WSL)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # uv, if not installed
cd ~/GitHub/rss-finance/model
uv sync                                              # Python 3.12 venv (repo root) + dependencies
curl -fsSL https://ollama.com/install.sh | sh       # Ollama, if not installed
ollama pull nomic-embed-text
ollama pull qwen3:14b
```

Settings live in `config.toml`; relative paths in it resolve against this folder.

## How it fits together

```
collector SQLite ──► articles ──► chunking ──► embeddings ──► store (LanceDB)
                                                                    │
question ──► retrieve (embed query, search, filter) ◄───────────────┘
                 │
                 ▼
             answer (prompt + Ollama chat model) ──► answer with cited URLs
```

| Module | Job |
|---|---|
| `config.py` | Load `config.toml` into typed settings |
| `articles.py` | Read articles from the collector's database (read-only) |
| `chunking.py` | Split articles into chunks that keep citation metadata |
| `embeddings.py` | Text → vectors via Ollama |
| `store.py` | LanceDB table: add chunks, search |
| `retrieve.py` | Question → ranked, filtered chunks |
| `answer.py` | Chunks + question → answer with citations |
| `cli.py` | `index`, `ask`, `search` commands |

Each module's docstring lists what it's responsible for and the design decisions to make.
For a step-by-step walkthrough, see [docs/TUTORIAL.md](docs/TUTORIAL.md).

## Suggested build order

1. `config.py` and `articles.py`, tested against `tests/fixtures/articles.json`
   until the collector has real data.
2. `chunking.py` with tests.
3. `embeddings.py` and `store.py`, then a `cli.py index` command.
4. `retrieve.py` and a `search` command, so you can judge retrieval on its own.
5. `answer.py` and the `ask` command.

Entity extraction and fine-tuning come later.

## Checks

Run from this folder:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```
