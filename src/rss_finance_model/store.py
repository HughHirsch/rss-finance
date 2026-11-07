"""Vector store backed by LanceDB.

Responsibility: open or create the chunks table, add chunks with their vectors, and search.

Decisions:
- Table schema: which metadata columns do you need to filter on (published time, source)
  and to cite (url, title)?
- Idempotency: running `index` twice must not duplicate chunks. What's the unique key, and
  do you skip, upsert or delete-and-replace an article that changed?
- Hybrid search: LanceDB can combine full-text (keyword) and vector search. Tickers such as
  "NVDA" match far better by keyword than by embedding.
- Filtering by time before or after the vector search, and what that does to top-k.

Docs: https://lancedb.github.io/lancedb/
"""
