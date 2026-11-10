"""Tests for chunking.

Cases worth covering (fixtures in tests/fixtures/articles.json):
- A short summary-only article (a3) becomes exactly one chunk.
- A long article (a1) splits into several chunks, none over the size limit.
- Consecutive chunks overlap by the configured amount.
- Every chunk keeps the article's id, url, title and published time.
- Empty or whitespace-only text doesn't produce empty chunks.
"""
