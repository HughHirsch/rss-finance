"""Command-line entry point.

Planned commands:
- `index`: read new articles, chunk, embed and add them to the store.
- `search "query"`: print the retrieved chunks without calling the chat model. Use this to
  tune chunking and retrieval before judging answers.
- `ask "question"`: retrieve, answer, and print the cited sources.

Once `main()` exists, add a `[project.scripts]` entry to pyproject.toml so
`uv run rss-finance-model ask "..."` works. argparse is enough; typer or click are optional.
"""
