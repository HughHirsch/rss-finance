"""Read articles from the rss-finance collector's SQLite database.

Responsibility: the only module that knows the collector's schema. Everything downstream works
with this repo's own article type (id, url, title, source, published time, text), so a schema
change in rss-finance only touches this file.

Decisions:
- Open the database read-only (an `sqlite3` URI with `mode=ro`) so this repo can never
  damage collected data, even while the collector is writing (it uses WAL).
- Incremental indexing: how do you find articles that aren't indexed yet? A high-water mark
  on an id or timestamp, or comparing against ids already in the index?
- Which text to use when an item only has the RSS summary, and when full text exists (M2)?
- Until the collector has real data, load `tests/fixtures/articles.json` through the same
  article type.

Docs: https://docs.python.org/3/library/sqlite3.html#sqlite3-uri-tricks
"""
