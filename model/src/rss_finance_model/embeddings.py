"""Turn text into vectors with a local embedding model served by Ollama.

Responsibility: wrap the Ollama embed call so nothing else depends on the Ollama client
directly. Swapping models (or adding another backend later) should only touch this file.

Decisions:
- Batching: how many texts per call, and how to report progress on a large first index.
- Ollama not running or model not pulled: fail fast with a message that says what to run.
- Task prefixes: nomic-embed-text expects "search_document: " on indexed text and
  "search_query: " on questions. Check the model card for whichever model you use.
- The vector dimension is fixed by the model. Changing models means rebuilding the index,
  so consider storing the model name alongside the index.

Docs: https://github.com/ollama/ollama-python
      https://ollama.com/library/nomic-embed-text
"""
