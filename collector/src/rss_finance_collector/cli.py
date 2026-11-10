"""Command line: `collect` and `stats`.

Responsibility: wire the other modules together. No fetching, parsing or SQL lives here.

Commands (once a `[project.scripts]` entry exists, `uv run rss-finance-collector collect`):
- `collect`: one pass over every feed, then exit. Log one line per feed (new items, 304,
  or error) and a summary. Exit non-zero only if *every* feed failed, so the scheduler can
  flag a broken run without one dead feed raising alarms forever.
- `stats`: items per feed per day for the last N days. This is how you notice a feed that
  went quiet or a gap from the machine being off.

Decisions:
- Where logs go (`data/collector.log`, gitignored by `*.log`) and how much to keep.
- argparse is enough; typer or click are optional.

Docs: https://docs.python.org/3/library/argparse.html, https://docs.python.org/3/library/logging.html
"""
