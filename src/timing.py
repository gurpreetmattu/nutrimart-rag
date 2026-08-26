"""
timing.py — a tiny reusable stage-timer.

Used by ask_hybrid.py's optional `timing` dict param (and search_hybrid.py's)
and by eval/benchmark_pipeline.py to build the latency comparison. Not wired
into ask.py/search_baseline.py — those stay untouched as the Phase 3 naive
control condition (see CLAUDE.md); baseline latency is measured as a single
black-box wall-clock duration around ask() instead, from the benchmark
script, not from inside ask.py itself.
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
