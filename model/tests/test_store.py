"""Tests for the LanceDB store.

Use pytest's `tmp_path` for the database, and fake vectors so tests don't need Ollama running.

Cases worth covering:
- Adding the same article twice leaves one set of chunks (idempotent re-index).
- Search returns chunks with their citation metadata intact.
- A time filter excludes the older article (a5).
- Decide and test what happens to an article with no published time (a4).
"""
