"""Tests for retrieval.

Cases worth covering:
- The same story from two sources (a1, a2) doesn't fill the results twice.
- Several matching chunks from one article are de-duplicated or grouped.
- A keyword query for a ticker ("GLBX") finds a3 even though the embedding may not.
- The default time window comes from config and can be overridden.
"""
