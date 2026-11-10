"""Split article text into chunks for embedding.

Responsibility: turn one article into a list of chunks. Each chunk carries what's needed to
cite it later: article id, url, title, source, published time and its position in the article.

Decisions:
- Unit: characters, words or tokens? The embedding model's context limit is in tokens.
- Overlap, and whether to break on sentence or paragraph boundaries.
- Many RSS items are a single short summary. Should those always be one chunk?
- Prepend the title to every chunk? In news, the headline often carries most of the signal.
- Pure functions with no I/O here make this the easiest module to test thoroughly.
"""
