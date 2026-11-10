"""Load settings from config.toml.

Responsibility: read config.toml once and hand typed settings to the rest of the package,
so no other module parses TOML or hard-codes a path or model name.

Relative paths (`articles.db_path`, `index.path`) resolve against the config file's folder,
so the CLI works from any working directory.

Docs: https://docs.python.org/3/library/tomllib.html
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.toml"


@dataclass(frozen=True)
class ArticlesSettings:
    db_path: Path


@dataclass(frozen=True)
class IndexSettings:
    path: Path
    table: str
    chunk_size: int
    chunk_overlap: int


@dataclass(frozen=True)
class ModelsSettings:
    embed: str
    chat: str


@dataclass(frozen=True)
class RetrievalSettings:
    top_k: int
    recent_days: int


@dataclass(frozen=True)
class Settings:
    articles: ArticlesSettings
    index: IndexSettings
    models: ModelsSettings
    retrieval: RetrievalSettings


class ConfigError(ValueError):
    """config.toml is missing a key or has an invalid value."""


def _section(raw: dict[str, Any], name: str, path: Path) -> dict[str, Any]:
    section = raw.get(name)
    if not isinstance(section, dict):
        raise ConfigError(f"{path}: missing [{name}] section")
    return section


def _get[T](section: dict[str, Any], section_name: str, key: str, kind: type[T], path: Path) -> T:
    if key not in section:
        raise ConfigError(f"{path}: missing key '{key}' in [{section_name}]")
    value = section[key]
    if not isinstance(value, kind) or isinstance(value, bool) and kind is int:
        raise ConfigError(
            f"{path}: [{section_name}].{key} must be {kind.__name__}, got {value!r}"
        )
    return value


def load_settings(path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    path = path.resolve()
    with path.open("rb") as f:
        raw = tomllib.load(f)
    base = path.parent

    articles = _section(raw, "articles", path)
    index = _section(raw, "index", path)
    models = _section(raw, "models", path)
    retrieval = _section(raw, "retrieval", path)

    settings = Settings(
        articles=ArticlesSettings(
            db_path=(base / _get(articles, "articles", "db_path", str, path)).resolve(),
        ),
        index=IndexSettings(
            path=(base / _get(index, "index", "path", str, path)).resolve(),
            table=_get(index, "index", "table", str, path),
            chunk_size=_get(index, "index", "chunk_size", int, path),
            chunk_overlap=_get(index, "index", "chunk_overlap", int, path),
        ),
        models=ModelsSettings(
            embed=_get(models, "models", "embed", str, path),
            chat=_get(models, "models", "chat", str, path),
        ),
        retrieval=RetrievalSettings(
            top_k=_get(retrieval, "retrieval", "top_k", int, path),
            recent_days=_get(retrieval, "retrieval", "recent_days", int, path),
        ),
    )

    if settings.index.chunk_size <= 0:
        raise ConfigError(f"{path}: [index].chunk_size must be positive")
    if not 0 <= settings.index.chunk_overlap < settings.index.chunk_size:
        raise ConfigError(f"{path}: [index].chunk_overlap must be in [0, chunk_size)")
    return settings
