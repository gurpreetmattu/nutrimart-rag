"""
timing.py — a tiny reusable stage-timer.

Used by ask_langchain_hybrid.py's optional `timing` dict param (and
retrieval/search_hybrid.py's/hybrid_core.py's) to instrument per-stage
latency — dense_search, bm25_search, rerank, query_rewrite, generation,
groundedness_check, total — surfaced in api/main_langchain.py's response
`timing` field. See ARCHITECTURE.md §10 for how it's exposed.
"""
import time
from contextlib import contextmanager


@contextmanager
def timed(store: dict | None, key: str):
    """
    No-op (zero overhead beyond the `if`) when `store` is None — every
    caller passes `timing=None` by default, so this only does anything when
    a caller opts in, matching the additive-param pattern already used for
    `resources`/`return_chunks` elsewhere in this pipeline.
    """
    if store is None:
        yield
        return
    start = time.perf_counter()
    yield
    store[key] = time.perf_counter() - start
