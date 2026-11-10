# Tutorial: building the RAG pipeline

You write the code; this walks you through it in order. Each step has a goal, numbered
instructions, a short *pattern* (generic names, not your finished function), and a check that
tells you when you're done. Do the steps in order: each one uses the previous one.

Commit after every step. Use `/hint` in Claude Code if you're stuck and `/review-mine`
when a step passes.

**Contents**

0. [Tooling](#step-0-tooling)
1. [Settings (`config.py`)](#step-1-settings-configpy)
2. [Articles (`articles.py`)](#step-2-articles-articlespy)
3. [Chunking (`chunking.py`)](#step-3-chunking-chunkingpy)
4. [Embeddings (`embeddings.py`)](#step-4-embeddings-embeddingspy)
5. [Vector store (`store.py`)](#step-5-vector-store-storepy)
6. [The `index` command (`cli.py`)](#step-6-the-index-command-clipy)
7. [Retrieval and `search` (`retrieve.py`)](#step-7-retrieval-and-search-retrievepy)
8. [Answers and `ask` (`answer.py`)](#step-8-answers-and-ask-answerpy)
9. [What next](#step-9-what-next)

---

## Step 0: Tooling

**Goal:** Python 3.12 venv, dependencies, and Ollama serving models on the GPU.

1. Install uv, then open a new shell so it's on your PATH:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. In the repo, create the venv and install everything:
   ```bash
   cd ~/GitHub/rss-finance/model
   uv sync
   ```
   uv downloads Python 3.12 for this project only, creates `.venv/` and writes `uv.lock`
   (both at the repo root, shared with the collector).
3. Install Ollama and pull both models:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull nomic-embed-text
   ollama pull qwen3:14b
   ```
4. Confirm the GPU is used: run `ollama run qwen3:14b "hi"`, then `ollama ps` in another shell.
5. Open the repo in VS Code (`code .`) and pick `.venv/bin/python` as the interpreter
   (Ctrl+Shift+P → *Python: Select Interpreter*).

**Check:**
- `uv run python --version` prints 3.12.x.
- `ollama ps` shows `100% GPU`.
- `uv run pytest` runs and reports *no tests collected*. That's expected for now.

**Commit:** `uv.lock`.

---

## Step 1: Settings (`config.py`)

**Goal:** one function, `load_settings(path)`, that returns typed, validated settings so no
other module reads TOML or hard-codes a path.

**Learn:** `tomllib`, `dataclasses` (frozen), `pathlib.Path`.

1. Create one frozen dataclass per section of `config.toml`: articles, index, models,
   retrieval. Field names should match the TOML keys.
2. Create a top-level `Settings` dataclass holding those four.
3. Write `load_settings(path: Path) -> Settings`:
   1. Open the file in **binary** mode (`"rb"`). `tomllib` requires it.
   2. Parse with `tomllib.load`.
   3. Build each section's dataclass from its dict.
   4. Resolve `db_path` and `index.path` relative to **the config file's folder**, not the
      current directory, so the CLI works from anywhere.
4. Decide what a missing key does. Letting the `KeyError`/`TypeError` surface is acceptable at
   this stage; a clearer message is a nice improvement.

**Pattern** (generic):
```python
@dataclass(frozen=True)
class Section:
    name: str
    size: int

raw = tomllib.load(fh)
section = Section(**raw["section"])
resolved = (config_path.parent / raw_path).resolve()
```

**Check:** write `tests/test_config.py`:
- Loading the repo's `config.toml` gives `settings.retrieval.top_k == 8`.
- `settings.articles.db_path` is an absolute `Path` ending in `articles.db`.
- Bonus: with `tmp_path`, write a config missing a section and assert it raises.

```bash
uv run pytest tests/test_config.py
uv run mypy src
```

---

## Step 2: Articles (`articles.py`)

**Goal:** this repo's own `Article` type and a loader for `tests/fixtures/articles.json`.
The SQLite reader comes later, once the collector exists, and returns the same type.

**Learn:** `datetime.fromisoformat`, timezone-aware datetimes, `json`.

1. Define a frozen `Article` dataclass: `id`, `url`, `title`, `source`, `published`, `text`.
   `published` is `datetime | None` because article `a4` has none.
2. Write `load_fixture_articles(path: Path) -> list[Article]`:
   1. Load the JSON list.
   2. For each item, build an `Article` from the keys you need. Ignore anything else
      (`_note` is there for you, not the code).
   3. Parse `published` with `datetime.fromisoformat` when it isn't `None`.
3. Make sure every datetime is **timezone-aware**. Comparing aware and naive datetimes raises
   `TypeError`, which would surface much later in retrieval.

**Pattern:**
```python
value = item.get("when")
when = datetime.fromisoformat(value) if value else None
assert when is None or when.tzinfo is not None
```

**Check:** `tests/test_articles.py`:
- 5 articles load.
- The article with id `a4` has `published is None`.
- Every other article's `published.tzinfo` is not `None`.

---

## Step 3: Chunking (`chunking.py`)

**Goal:** `chunk_article(article, size, overlap) -> list[Chunk]`, pure and fully tested.

**Learn:** test-first development; sliding windows.

1. **Write the tests first.** Turn each case listed in `tests/test_chunking.py` into a test
   function. Run them and watch them fail.
2. Define a frozen `Chunk` dataclass: a stable `chunk_id`, `article_id`, `position` (0, 1, 2…),
   `text`, plus the citation fields copied from the article (`url`, `title`, `source`,
   `published`).
3. Choose a stable `chunk_id`. `f"{article_id}:{position}"` is enough. It must be the same
   every time you re-index the same article; Step 5 relies on that.
4. Decide your unit. **Characters** is simplest to start with. You can switch to words or
   tokens later without changing anything outside this module.
5. Implement:
   1. Short text (length ≤ size) → exactly one chunk.
   2. Otherwise slide a window of `size`, stepping by `size - overlap`.
   3. Skip chunks that are empty after `.strip()`.
6. Prepend the title to each chunk's text (e.g. `"{title}\n\n{text}"`). In news the headline
   carries a lot of signal. Keep it simple: one line of code, not a framework.

**Pattern** (sliding window):
```python
step = size - overlap
for start in range(0, len(text), step):
    piece = text[start:start + size]
    ...
    if start + size >= len(text):
        break
```

**Check:** all chunking tests pass. Validate: `overlap >= size` would loop forever or step
backwards. Raise `ValueError` for it, and add a test.

**Improvement for later:** break on paragraph or sentence boundaries instead of mid-word.

---

## Step 4: Embeddings (`embeddings.py`)

**Goal:** `embed_documents(texts) -> list[list[float]]` and `embed_query(text) -> list[float]`,
the only place that talks to Ollama for embeddings.

**Learn:** the `ollama` Python client, batching, task prefixes.

1. Read the [nomic-embed-text model card](https://ollama.com/library/nomic-embed-text).
   It expects `"search_document: "` before indexed text and `"search_query: "` before a
   question. Getting this wrong quietly lowers retrieval quality.
2. Use `ollama.embed(model=..., input=[...])`. It takes a list and returns one vector per
   input in `.embeddings`.
3. Batch: send e.g. 32 texts per call rather than one at a time.
4. Fail fast: catch the connection error when Ollama isn't running and raise one with a
   message telling you to run `ollama serve`.
5. Pass the model name in (from settings) rather than hard-coding it.

**Pattern:**
```python
response = client.embed(model=model_name, input=batch)
vectors.extend(response.embeddings)
```

**Check:** a quick script or test (mark it so it can be skipped when Ollama is down):
- Two texts give two vectors of the same length (768 for nomic-embed-text).
- "chip maker earnings beat" is closer (cosine similarity) to article `a1` than to `a5`.
  This is the moment embeddings stop being abstract. Compute the cosine yourself.

---

## Step 5: Vector store (`store.py`)

**Goal:** open/create a LanceDB table, upsert chunks with vectors, and search with a time filter.

**Learn:** [LanceDB](https://lancedb.github.io/lancedb/) tables, schemas, `merge_insert`,
filtering.

1. Decide the row layout: `chunk_id`, `article_id`, `url`, `title`, `source`, `published`,
   `text`, `vector`.
2. **Store `published` as an int (Unix seconds)**, with a sentinel or nullable for `a4`.
   Integer comparisons make time filters simple. Decide now what a missing date means for
   filtering (excluded from "last 7 days"? always included?) and write it down in a docstring.
3. Define the schema, either with pyarrow or LanceDB's pydantic `LanceModel` with a
   `Vector(768)` field.
4. `open_store(path, table_name)`: `lancedb.connect(path)`, then create the table if it doesn't
   exist (`exist_ok=True`) or open it.
5. `upsert(rows)`: use `merge_insert` keyed on `chunk_id` so re-indexing updates instead of
   duplicating. This is why Step 3's ids had to be stable.
6. `search(vector, k, since)`: vector search with a `where` filter on `published`, limited to
   `k`, returning plain dicts or your own result type.

**Pattern:**
```python
db = lancedb.connect(path)
table = db.create_table(name, schema=Schema, exist_ok=True)
table.merge_insert("key").when_matched_update_all().when_not_matched_insert_all().execute(rows)
hits = table.search(query_vector).where("ts >= 1700000000", prefilter=True).limit(k).to_list()
```

**Check** (`tests/test_store.py`, using `tmp_path` and **fake vectors** like `[1.0] + [0.0]*767`,
so no Ollama needed):
- Upserting the same rows twice → `table.count_rows()` unchanged.
- A search with `since` = 7 days before the newest fixture date excludes `a5`.
- Results keep `url` and `title`.

---

## Step 6: The `index` command (`cli.py`)

**Goal:** `uv run rss-finance-model index` loads articles, chunks, embeds and upserts them.

**Learn:** `argparse` subcommands, `[project.scripts]`.

1. Write `main(argv: list[str] | None = None) -> int` with an `argparse` parser and a
   subparser per command. Start with `index` only.
2. Add a `--fixtures` flag so `index` reads `tests/fixtures/articles.json` until the collector
   exists. Later, the default switches to the SQLite reader.
3. The `index` flow: load settings → load articles → chunk each → embed all chunk texts
   (as documents) → build rows → upsert → print a summary (articles, chunks, seconds taken).
4. Register the command in `pyproject.toml`:
   ```toml
   [project.scripts]
   rss-finance-model = "rss_finance_model.cli:main"
   ```
   then run `uv sync` again.

**Pattern:**
```python
parser = argparse.ArgumentParser(prog="tool")
sub = parser.add_subparsers(dest="command", required=True)
run_cmd = sub.add_parser("run")
run_cmd.add_argument("--flag", action="store_true")
args = parser.parse_args(argv)
```

**Check:**
```bash
uv run rss-finance-model index --fixtures
uv run rss-finance-model index --fixtures   # second run: same chunk count, no duplicates
```

---

## Step 7: Retrieval and `search` (`retrieve.py`)

**Goal:** question in, ranked chunks out, and a `search` command to inspect them **before**
any chat model is involved.

1. `retrieve(question, settings, since=None)`:
   1. Embed the question with `embed_query` (query prefix!).
   2. Default `since` to now minus `recent_days`. Allow an override.
   3. Search the store for more than you need (e.g. `top_k * 3`).
   4. **De-duplicate by article**: keep the best chunk per `article_id`, then take `top_k`.
2. Add a `search "query" [--days N]` command that prints rank, distance, title, source, date
   and the first ~100 characters of each chunk.
3. Note: the fixture articles are dated November 2026. Use `--days 365` when testing, or
   your 7-day window will be empty depending on today's date.

**Check:** try these and judge the results yourself:
- `search "chip company earnings"` → `a1`/`a2` on top.
- `search "GLBX"` → does `a3` show up? If not, you've just found why hybrid (keyword +
  vector) search exists. Keep the note for Step 9.

---

## Step 8: Answers and `ask` (`answer.py`)

**Goal:** `ask "question"` prints a grounded answer with numbered citations and their URLs.

**Learn:** prompt construction, `ollama.chat`, mapping citations back to sources.

1. Build the prompt:
   1. A system message: answer only from the numbered articles below; cite like `[1]`;
      if they don't contain the answer, say so.
   2. Today's date.
   3. The retrieved chunks, numbered `[1]…[k]`, each with title, source and published date.
   4. The question.
2. Call `ollama.chat(model=..., messages=[...])` and read the reply text.
3. Find the `[n]` references in the reply with a regex, map each to its chunk's URL, and
   print a *Sources* list. Ignore numbers that don't exist and log a warning; models do
   invent citations.
4. Wire up the `ask` command. Streaming is optional (`stream=True` gives you parts to print
   as they arrive).

**Pattern** (citation extraction):
```python
cited = {int(n) for n in re.findall(r"\[(\d+)\]", reply)}
valid = sorted(n for n in cited if 1 <= n <= len(sources))
```

**Check:**
- `ask "What happened with Acme Semiconductor's earnings?" --days 365` cites `a1` and/or `a2`.
- `ask "What is the weather in Paris?"` says the articles don't cover it instead of guessing.

**Commit.** You have a working local RAG pipeline.

---

## Step 9: What next

In rough priority order:

1. **Collector.** Build the rss-finance collector and the SQLite reader in `articles.py`, then
   drop `--fixtures`. Real data shows what actually needs tuning.
2. **Hybrid search.** Add a LanceDB full-text index on `text` and combine keyword and vector
   results, so tickers like `GLBX` match.
3. **Evaluation.** Write 20 real questions with the articles that should answer them, and
   measure how often retrieval finds them. Tune chunk size, `top_k` and the time window
   against that, not by feel.
4. **Better chunking.** Sentence or paragraph boundaries.
5. **Entity extraction** for TickerGraph (M3), once retrieval is solid.
