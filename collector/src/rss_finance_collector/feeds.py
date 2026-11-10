"""Load the feed list from `feeds.toml`.

Responsibility: turn `feeds.toml` into a list of typed feed entries (name, url). No other
module parses the file.

Decisions:
- Validate early: missing `name` or `url`, duplicate names, duplicate URLs. A typo here means
  silently missing data for weeks.
- Where the file lives by default (next to the package, like the model's `config.toml`)?
- Is `name` stable? It becomes the article's `source`, so renaming a feed splits its history.

Docs: https://docs.python.org/3/library/tomllib.html
"""
