"""SQLite storage: the contract with the model package.

Responsibility: the only module that writes `data/articles.db`. The model reads it through
`model/src/rss_finance_model/articles.py`, which expects for each article:
`id`, `url`, `title`, `source`, `published` (may be NULL), `text`.

Decisions:
- Schema: an `articles` table with those columns plus `guid`, `feed`, `fetched_at`,
  `summary` and `raw_json`; a `feeds` table for per-feed HTTP state (`etag`, `last_modified`,
  last success, last error); maybe a `runs` table for health checks.
- Store timestamps as ISO 8601 UTC text, so the model's `datetime.fromisoformat` reads them.
- Dedupe in the database, not in Python: a UNIQUE constraint on the dedupe key and
  `INSERT ... ON CONFLICT DO NOTHING`, so re-running a pass is always safe.
- `PRAGMA journal_mode=WAL`, so the model can read while the collector writes.
- One transaction per feed: a crash mid-run leaves whole feeds, never half of one.
- How the schema evolves later: `PRAGMA user_version` plus small migration steps.

Docs: https://www.sqlite.org/lang_upsert.html, https://www.sqlite.org/wal.html
"""
