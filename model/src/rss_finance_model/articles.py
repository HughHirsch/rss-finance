"""Read articles from the rss-finance collector's SQLite database.

Responsibility: the only module that knows the collector's schema. Everything downstream works
with this repo's own `Article` type, so a schema change in rss-finance only touches this file.

The collector has no schema yet, so `read_articles` assumes an `articles` table with columns
`id, url, title, source, published, text`; `published` is ISO 8601 text (UTC) or NULL. Adjust
`_QUERY` once the collector's real schema exists. Until then, use `load_fixture`.

The database is opened read-only (`mode=ro`) so this repo can never damage collected data.
Incremental indexing is left to the caller: it passes `since` (published time) and/or
compares ids against what is already in the index.

Docs: https://docs.python.org/3/library/sqlite3.html#sqlite3-uri-tricks
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_QUERY = "SELECT id, url, title, source, published, text FROM articles"


@dataclass(frozen=True)
class Article:
    id: str
    url: str
    title: str
    source: str
    published: datetime | None
    text: str


def parse_published(value: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp to an aware UTC datetime; None if missing or invalid."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _from_row(row: dict[str, object]) -> Article:
    published = row.get("published")
    return Article(
        id=str(row["id"]),
        url=str(row["url"]),
        title=str(row.get("title") or ""),
        source=str(row.get("source") or ""),
        published=parse_published(published if isinstance(published, str) else None),
        text=str(row.get("text") or ""),
    )


def load_fixture(path: Path) -> list[Article]:
    """Load articles from a JSON fixture (a list of objects with the Article fields)."""
    with path.open(encoding="utf-8") as f:
        return [_from_row(item) for item in json.load(f)]


def read_articles(db_path: Path, since: datetime | None = None) -> Iterator[Article]:
    """Yield articles from the collector's database, oldest first.

    With `since`, only articles published at or after it are returned; articles without a
    published time are always included so they are not silently skipped.
    """
    conn = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        for row in conn.execute(f"{_QUERY} ORDER BY published"):
            article = _from_row(dict(row))
            if since and article.published and article.published < since:
                continue
            yield article
    finally:
        conn.close()
