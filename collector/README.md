# collector

Fetches financial-news RSS feeds on a schedule and stores every new item in SQLite at
`data/articles.db` (repo root). The model package reads that database; nothing else writes it.

Step-by-step guide: [../docs/COLLECTOR.md](../docs/COLLECTOR.md).

| Module | Job |
|---|---|
| `feeds.py` | Load the feed list from `feeds.toml` |
| `fetch.py` | Fetch one feed with conditional GET, timeouts and error handling |
| `normalize.py` | Turn a feed entry into one clean row |
| `store.py` | SQLite schema, WAL, dedupe, per-feed HTTP cache state |
| `cli.py` | `collect` (one pass over all feeds) and `stats` (daily counts per feed) |

Each module's docstring lists its responsibility and the decisions to make.

The collector runs **one pass and exits**. Scheduling lives outside the code (Task Scheduler,
cron, or a Lambda schedule), which keeps it simple to test and to move.

## Checks

Run from this folder:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```
