"""
retrieval/test_search_hybrid.py — regression tests for search_hybrid.py's
pure, no-Qdrant/no-model logic: _ins_codes_of() (compound ins_no splitting,
Finding 31), _fuse()'s new bm25_score plumbing (Finding 34, the q27 fix's
dependency), _detect_query_class()/_get_class_ins_index() (Finding 36's
functional-class exclusion), and find_comparison_group_match() (Finding 16).

No pytest in this project — plain assertions + a __main__ runner, same
convention as api/test_security.py and generation/test_token_budget.py.
Every check here is offline (no Qdrant, no embedding/cross-encoder model, no
LLM call) — it only locks in the pure-function contracts these bug fixes
depend on, not the live retrieval pipeline itself (that's what the eval
scripts and this session's manual live verification cover).

Run:
    python src/retrieval/test_search_hybrid.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.parse_kb import Chunk
from retrieval.search_hybrid import (
    _ins_codes_of, _fuse, _detect_query_class, _get_class_ins_index,
    find_comparison_group_match,
)

_failures: list[str] = []


def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


# --- _ins_codes_of: compound ins_no splitting (Finding 31) -----------------

check("splits a slash-separated compound ins_no", _ins_codes_of("627/631/635") == {"627", "631", "635"})
check("splits a comma-separated compound ins_no with parenthetical suffixes",
      _ins_codes_of("450(i), 451(i), 452(i)") == {"450(i)", "451(i)", "452(i)"})
check("a single code splits to a one-element set", _ins_codes_of("223") == {"223"})
check("an empty ins_no splits to an empty set", _ins_codes_of("") == set())
check("the real Finding-31 bug case: a compound code intersects the individual code it covers",
      bool(_ins_codes_of("627/631/635") & {"631"}))
check("the pre-fix behavior would have failed this: the whole string never equals a single code",
      "627/631/635" not in {"627", "631", "635"})

print()

# --- _fuse: bm25_score plumbing (Finding 34, the q27 fix's dependency) -----


def _mk_chunk(chunk_id: str, source_file: str = "test.md") -> Chunk:
    return Chunk(chunk_id=chunk_id, source_file=source_file, heading=chunk_id, text="dummy text")


dense_results = [
    {"chunk_id": "a", "source_file": "test.md", "heading": "a", "text": "t", "doc_type": "", "entity": "",
     "ins_no": "", "comparison_group": ""},
    {"chunk_id": "b", "source_file": "test.md", "heading": "b", "text": "t", "doc_type": "", "entity": "",
     "ins_no": "", "comparison_group": ""},
]
bm25_results = [
    (_mk_chunk("a"), 16.398),   # also in dense_results — real bm25 score should attach
    (_mk_chunk("c"), 10.841),   # bm25-only chunk — should appear with a real score, no dense rrf contribution beyond bm25's own
]

fused = _fuse(dense_results, bm25_results)

check("a chunk found by both dense and BM25 carries BM25's real raw score",
      fused["a"]["bm25_score"] == 16.398)
check("a chunk found only by dense defaults bm25_score to 0.0", fused["b"]["bm25_score"] == 0.0)
check("a chunk found only by BM25 carries its real raw score", fused["c"]["bm25_score"] == 10.841)
check("a chunk found by both dense and BM25 has a combined (non-zero) rrf_score", fused["a"]["rrf_score"] > 0)
check("every fused chunk has a chunk_id matching its dict key",
      all(cid == c["chunk_id"] for cid, c in fused.items()))

print()

# --- _detect_query_class / _get_class_ins_index (Finding 36) ---------------

class_index = _get_class_ins_index()

check("_get_class_ins_index() parses the real KB and finds the Colours class",
      "Colours" in class_index and len(class_index["Colours"]) > 0)
check("_get_class_ins_index() correctly places INS 160c under Colours",
      "160c" in class_index.get("Colours", set()))
check("_get_class_ins_index() correctly places INS 223 under Preservatives",
      "223" in class_index.get("Preservatives", set()))
check("_get_class_ins_index() correctly places the flavour-enhancer group under Flavour Enhancers",
      {"627", "631", "635"} <= class_index.get("Flavour Enhancers", set()))

check("'colour additive' detects the Colours class", _detect_query_class("what is the colour additive limit") == "Colours")
check("'the flavour enhancer' detects Flavour Enhancers",
      _detect_query_class("is the flavour enhancer within limit") == "Flavour Enhancers")
check("'anticaking agent' detects Anticaking / Flour Treatment",
      _detect_query_class("what is the anticaking agent maximum") == "Anticaking / Flour Treatment")
check("a query naming no functional class returns None",
      _detect_query_class("how many calories are in Parle-G") is None)
check("longest-phrase-first: 'anti-caking agent' (hyphenated) still matches",
      _detect_query_class("the anti-caking agent limit") == "Anticaking / Flour Treatment")

print()

# --- find_comparison_group_match (Finding 16) -------------------------------

paired = [
    {"chunk_id": "x1", "source_file": "fssai_knowledge_base.md", "comparison_group": "sugar_vs_sweetener"},
    {"chunk_id": "x2", "source_file": "nutrition_knowledge_base.md", "comparison_group": "sugar_vs_sweetener"},
]
same_file_pair = [
    {"chunk_id": "y1", "source_file": "nutrition_knowledge_base.md", "comparison_group": "sugar_vs_sweetener"},
    {"chunk_id": "y2", "source_file": "nutrition_knowledge_base.md", "comparison_group": "sugar_vs_sweetener"},
]
no_tag = [
    {"chunk_id": "z1", "source_file": "fssai_knowledge_base.md", "comparison_group": ""},
]

check("a real cross-file tagged pair is found", find_comparison_group_match(paired) is not None)
check("a same-file-only tagged pair is correctly rejected (Finding 16's q09 false-positive fix)",
      find_comparison_group_match(same_file_pair) is None)
check("candidates with no tag at all produce no match", find_comparison_group_match(no_tag) is None)
check("an empty candidate list produces no match", find_comparison_group_match([]) is None)

print()
if _failures:
    print(f"{len(_failures)} FAILURE(S):")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All search_hybrid regression checks passed.")
