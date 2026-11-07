"""Load settings from config.toml.

Responsibility: read config.toml once and hand typed settings to the rest of the package,
so no other module parses TOML or hard-codes a path or model name.

Decisions:
- Representation: frozen dataclasses, TypedDict or pydantic? (stdlib is enough here.)
- Relative paths: resolve against the repo root, the config file's folder or the CWD?
  `db_path` points into the sibling rss-finance repo, so this matters.
- Missing or invalid keys: fail at startup with a clear message, not deep inside indexing.

Docs: https://docs.python.org/3/library/tomllib.html
"""
