"""Fetch one feed.

Responsibility: one HTTP fetch per feed per run, polite and failure-tolerant. Returns the
parsed entries plus the new cache validators, or a clear error. One bad feed must never stop
the run.

Decisions:
- Conditional GET: send the `ETag` / `Last-Modified` saved from the last run, and treat
  `304 Not Modified` as "nothing new" (feedparser's `etag=` and `modified=` arguments do this).
- Timeouts and a descriptive User-Agent. No retries inside a run; the next scheduled run is
  the retry.
- What counts as a failure worth logging: network errors, HTTP 4xx/5xx, and feedparser's
  `bozo` flag (malformed XML that may still have usable entries).

Docs: https://feedparser.readthedocs.io/en/latest/http-etag.html
"""
