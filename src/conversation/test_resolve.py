"""
conversation/test_resolve.py — regression tests for resolve_followup(),
focused on the "bare definitional question" bug found live 2026-08-28.

Confirmed real, live: with Britannia Brown Bread as the active product,
"what is maida?" got rewritten to "For Britannia Brown Bread: what is
maida?" — this module's own docstring already documents the general root
cause (product-name-heavy phrasing drags the cross-encoder toward that
product's own ingredient/additive chunks over generic guidance content)
for the value-judgment rewrite branch, but the fix was never extended to
the plain product-name-prepend branch. Live result: retrieval returned
Brown Bread's own unrelated additive chunks instead of
ingredient_kb_tier2.md's real "Refined wheat flour (maida)" entry, and the
answer wrongly claimed maida "isn't defined" in the retrieved context.

No pytest in this project — plain assertions + a __main__ runner, same
convention as every other test_*.py file here. Pure template-rewrite
checks: no LLM call, no Qdrant, no quota cost.

Run:
    python src/conversation/test_resolve.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conversation.state import default_state, set_product
from conversation.resolve import resolve_followup

_failures: list[str] = []


def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


_state = default_state()
set_product(_state, "britannia_brown_bread", "Britannia Brown Bread")

# --- Bare definitional questions must stay product-name-free ---------------
for q in ["what is maida?", "what is wheat?", "what are preservatives?"]:
    resolved = resolve_followup(q, _state)
    check(f"definitional question left unresolved: {q!r} -> {resolved!r}", resolved == q)

# --- Genuine product follow-ups must still get the product name prepended --
_genuine_followups = [
    "what is this ingredient",
    "what is the sugar content of this",
    "what is the pack size",
    "is it safe?",
    "does it contain milk?",
]
for q in _genuine_followups:
    resolved = resolve_followup(q, _state)
    check(f"genuine follow-up still scoped to product: {q!r} -> {resolved!r}",
          resolved == f"For Britannia Brown Bread: {q}")


if __name__ == "__main__":
    print(f"\n{len(_failures)} failure(s)." if _failures else "\nAll resolve_followup regression checks passed.")
    sys.exit(1 if _failures else 0)
