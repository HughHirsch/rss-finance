"""Find the chunks most relevant to a question.

Responsibility: question in, ranked chunks out. Embeds the query, searches the store and
applies filters. Keep it independent of the chat model so retrieval can be judged on its own
(the `search` command).

Decisions:
- Default time window (`recent_days` in config.toml) and how a caller overrides it.
- De-duplication: several top chunks from one article, or the same story from several sources.
- Recency vs. relevance: should a slightly less relevant article from today beat one from
  last week?
- Later, if top-k quality is poor: a reranker on the top results.
"""
