# Tutorial: building the collector (M1)

You write the code; this walks you through it in order. Each step has a goal, numbered
instructions, a short *pattern* (generic names, not your finished function), and a check that
tells you when you're done. Do the steps in order: each one uses the previous one.

Commit after every step. Use `/hint` in Claude Code if you're stuck and `/review-mine`
when a step passes.

**Why this comes first:** most RSS feeds only show their last 20–50 items. Anything you
don't collect now is gone for good, and the model needs weeks of history to be useful.
Aim for a minimal collector in 2–4 evenings, running unattended, then leave it alone.

**Rule of thumb:** capture now anything you can't recover later (the raw entry, when you
fetched it, a broad feed list). Anything you can derive later (clean text, chunks,
embeddings, entities) can wait.

**Contents**

0. [Tooling](#step-0-tooling)
1. [Feed list (`feeds.py`)](#step-1-feed-list-feedspy)
2. [Storage (`store.py`)](#step-2-storage-storepy)
3. [Normalizing entries (`normalize.py`)](#step-3-normalizing-entries-normalizepy)
4. [Fetching (`fetch.py`)](#step-4-fetching-fetchpy)
5. [The `collect` command (`cli.py`)](#step-5-the-collect-command-clipy)
6. [The `stats` command](#step-6-the-stats-command)
7. [Running unattended](#step-7-running-unattended)
8. [Connecting the model](#step-8-connecting-the-model)

---

## Step 0: Tooling

**Goal:** the collector package installed in the workspace venv.

1. Install uv if you haven't: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then open a
   new shell.
2. Sync the collector:
   ```bash
   cd ~/GitHub/rss-finance/collector
   uv sync
   ```
   The venv lives at the repo root (`.venv/`) and is shared with the model package.
3. In VS Code, open the repo root and pick `.venv/bin/python` as the interpreter.

**Check:** `uv run python -c "import feedparser; print(feedparser.__version__)"` works, and
`uv run pytest` reports *no tests collected*.

**Commit:** `uv.lock` (at the repo root).

---

## Step 1: Feed list (`feeds.py`)

**Goal:** `load_feeds(path) -> list[Feed]` with validation, and a real feed list.

**Learn:** `tomllib`, frozen dataclasses.

1. Pick 8–15 feeds: a mix of markets news, company news and macro. Open each URL, check it
   updates several times a day, and skim the site's terms for automated access.
2. Add them to `feeds.toml` in the `[[feed]]` format shown there.
3. Define a frozen `Feed` dataclass (`name`, `url`) and `load_feeds`.
4. Reject: a missing key, an empty list, duplicate names, duplicate URLs. Raise one error type
   with the file path in the message.

**Pattern:**
```python
with path.open("rb") as f:
    raw = tomllib.load(f)
items = [Thing(**entry) for entry in raw.get("thing", [])]
```

**Check:** `tests/test_feeds.py` passes for a valid file, a duplicate name, and a missing URL
(write small TOML files into pytest's `tmp_path`).

---

## Step 2: Storage (`store.py`)

**Goal:** create the database, insert items idempotently, and keep per-feed HTTP state.

**Learn:** SQLite UPSERT, WAL mode, transactions, `PRAGMA user_version`.

1. Write `connect(path)` that creates parent folders, opens the database, and turns on WAL.
2. Write `init_schema(conn)` that creates the tables listed in `store.py`'s docstring if they
   don't exist, and sets `user_version = 1`.
3. Write `insert_items(conn, items) -> int` that inserts with `ON CONFLICT DO NOTHING` and
   returns how many rows were new.
4. Write `get_http_state(conn, feed)` and `save_http_state(conn, feed, etag, modified, error)`.
5. Read `model/src/rss_finance_model/articles.py` and make sure your columns give it what it
   needs: `id`, `url`, `title`, `source`, `published`, `text`.

**Pattern:**
```python
conn.execute("PRAGMA journal_mode=WAL")
with conn:  # one transaction
    cur = conn.executemany(
        "INSERT INTO things (key, value) VALUES (?, ?) ON CONFLICT(key) DO NOTHING", rows
    )
```

**Check:** `tests/test_store.py`:
- Inserting the same two items twice leaves 2 rows, and the second call returns 0.
- `PRAGMA journal_mode` returns `wal`.
- HTTP state round-trips.

---

## Step 3: Normalizing entries (`normalize.py`)

**Goal:** `normalize(entry, feed, fetched_at) -> Item`, tested against saved feed files.

**Learn:** feedparser's entry fields, `time.struct_time` → aware `datetime`, URL parsing.

1. Save two or three real feed responses into `tests/fixtures/` (one RSS, one Atom). Add a
   tiny hand-written one with a missing date and a URL with `utm_` parameters.
2. Parse them in tests with `feedparser.parse(path)`. No network in tests.
3. Pick the dedupe key, strip tracking parameters, convert dates to UTC, strip HTML from the
   summary, and keep the raw entry as JSON.

**Pattern:**
```python
ts = entry.get("published_parsed") or entry.get("updated_parsed")
when = datetime(*ts[:6], tzinfo=UTC) if ts else None
parts = urlsplit(url)
query = [(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")]
```

**Check:** `tests/test_normalize.py`:
- An entry without a date gives `published is None`, never "now".
- The `utm_` URL comes out clean.
- Every datetime is timezone-aware.

---

## Step 4: Fetching (`fetch.py`)

**Goal:** `fetch(feed, etag, modified) -> FetchResult` that never raises for an ordinary
failure.

**Learn:** conditional GET, feedparser's `status`, `etag`, `modified` and `bozo`.

1. Call `feedparser.parse(url, etag=..., modified=..., agent=...)` with a descriptive
   User-Agent.
2. Map the outcome to one result type: new entries, not modified (304), or error with a
   message. Malformed feeds (`bozo`) with usable entries count as success plus a warning.
3. Return the new `etag` / `modified` to save.

**Pattern:**
```python
result = feedparser.parse(url, etag=etag, modified=modified, agent=agent)
if result.get("status") == 304:
    return NotModified()
```

**Check:** run it by hand against two real feeds twice in a row. The second run should get a
304 from at least one of them.

---

## Step 5: The `collect` command (`cli.py`)

**Goal:** `uv run rss-finance-collector collect` does one full pass and exits.

1. Add a script entry to `collector/pyproject.toml`:
   ```toml
   [project.scripts]
   rss-finance-collector = "rss_finance_collector.cli:main"
   ```
   then `uv sync`.
2. For each feed: load HTTP state, fetch, normalize, insert, save state. One transaction per
   feed. Catch and log per-feed errors; keep going.
3. Log one line per feed and a summary to stdout and `data/collector.log`.
4. Exit code: non-zero only if every feed failed.

**Check:** run `collect` twice. The first run stores items; the second stores 0 or a few new
ones, and nothing is duplicated.

---

## Step 6: The `stats` command

**Goal:** `uv run rss-finance-collector stats --days 7` prints items per feed per day.

1. One `GROUP BY feed, date(fetched_at)` query.
2. Print a small table; flag feeds with zero items on a day.

**Check:** the numbers match a manual `SELECT count(*)` for one feed.

---

## Step 7: Running unattended

**Goal:** the collector runs every 30 minutes without you.

WSL isn't a server: it stops when nothing is using it, and nothing runs while the PC sleeps.
Gaps lose data permanently, so pick deliberately:

1. **Windows Task Scheduler** (quickest). Create a task that runs every 30 minutes:
   - Program: `wsl.exe`
   - Arguments: `-d Ubuntu -e bash -lc "cd ~/GitHub/rss-finance/collector && ~/.local/bin/uv run rss-finance-collector collect"`
   - Settings: run whether the user is logged on or not; don't start a new instance if one is
     running. Gaps happen while the PC is off.
2. **Always-on box** (Raspberry Pi or small VPS): clone the repo, `uv sync` in `collector/`,
   add a cron entry. Most reliable for the effort.
3. **AWS Lambda on an EventBridge schedule** writing to S3: reliable, near free, good cert
   practice, but needs a sync step to get the database back for the model.

**Check (M1 done):** it has run unattended for 48 hours and `stats` shows steady counts for
every feed.

---

## Step 8: Connecting the model

**Goal:** the model reads real articles.

1. Confirm `model/config.toml` points at `../data/articles.db`.
2. Write the SQLite reader in `model/src/rss_finance_model/articles.py` (read-only URI,
   `mode=ro`), returning the same `Article` type as the fixture loader.
3. Continue with [model/docs/TUTORIAL.md](../model/docs/TUTORIAL.md).
