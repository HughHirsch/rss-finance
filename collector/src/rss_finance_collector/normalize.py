"""Turn a feed entry into one clean row.

Responsibility: map feedparser's loose entry dicts to this package's own item type, with
every field the model needs (see `store.py` for the contract).

Decisions:
- The dedupe key: entry `id`/GUID when present, otherwise the URL. Normalize URLs first
  (strip `utm_*` tracking parameters) so the same story isn't stored twice.
- `published`: use `published_parsed`, fall back to `updated_parsed`, else `None`. Always
  timezone-aware UTC. Never invent a date.
- `fetched_at` comes from the run, not the feed: it records when you could first have known.
- Keep the raw entry (as JSON) so anything you didn't extract today can be recovered later.
- `text` is the RSS summary for now, with HTML stripped. Full text is milestone M2.

Docs: https://feedparser.readthedocs.io/en/latest/reference.html
"""
