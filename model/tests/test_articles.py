"""Tests for config loading and article reading."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rss_finance_model.articles import load_fixture, parse_published, read_articles
from rss_finance_model.config import ConfigError, load_settings

FIXTURE = Path(__file__).parent / "fixtures" / "articles.json"
CONFIG = Path(__file__).parents[1] / "config.toml"


def test_fixture_loads_all_articles() -> None:
    articles = load_fixture(FIXTURE)
    assert [a.id for a in articles] == ["a1", "a2", "a3", "a4", "a5"]
    assert articles[0].published == datetime(2026, 11, 5, 13, 30, tzinfo=UTC)


def test_missing_published_is_none() -> None:
    a4 = next(a for a in load_fixture(FIXTURE) if a.id == "a4")
    assert a4.published is None


def test_parse_published_handles_bad_input() -> None:
    assert parse_published(None) is None
    assert parse_published("not a date") is None
    assert parse_published("2026-11-05T13:30:00") == datetime(2026, 11, 5, 13, 30, tzinfo=UTC)


def test_read_articles_since_keeps_undated(tmp_path: Path) -> None:
    db = tmp_path / "articles.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE articles (id TEXT, url TEXT, title TEXT, source TEXT, published TEXT, text TEXT)"
    )
    conn.executemany(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("1", "https://x/1", "old", "S", "2026-10-01T00:00:00Z", "t"),
            ("2", "https://x/2", "new", "S", "2026-11-05T00:00:00Z", "t"),
            ("3", "https://x/3", "undated", "S", None, "t"),
        ],
    )
    conn.commit()
    conn.close()

    since = datetime(2026, 11, 1, tzinfo=UTC)
    # SQLite sorts NULL first, so the undated article leads; it is never dropped by `since`.
    assert [a.id for a in read_articles(db, since)] == ["3", "2"]
    assert len(list(read_articles(db))) == 3


def test_load_settings_resolves_paths_against_config_folder() -> None:
    settings = load_settings(CONFIG)
    assert settings.articles.db_path == (CONFIG.parent / "../data/articles.db").resolve()
    assert settings.index.path == (CONFIG.parent / "data/index").resolve()
    assert settings.models.chat == "qwen3:14b"


def test_load_settings_rejects_missing_key(tmp_path: Path) -> None:
    bad = tmp_path / "config.toml"
    bad.write_text("[articles]\n")
    with pytest.raises(ConfigError, match="missing key 'db_path'"):
        load_settings(bad)
