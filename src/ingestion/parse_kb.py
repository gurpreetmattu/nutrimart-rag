"""
parse_kb.py — Baseline (deliberately naive) markdown KB parser.

Splits each KB markdown file on ## and ### headers into chunks. No smart
handling of tables, no chunk-size optimization, no overlap. This is
intentional: Phase 3 is the naive baseline for the eval comparison in
Phase 7. Phase 5's hybrid pipeline can revisit chunking strategy.
"""
import re
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str          # e.g. "fssai_knowledge_base.md::chunk_012"
    source_file: str       # e.g. "fssai_knowledge_base.md"
    heading: str           # the header text, e.g. "Chunk 12" or "INS 472e"
    text: str              # full chunk text including heading
    doc_type: str = ""     # extracted from the Metadata line if present
    entity: str = ""       # extracted from the Metadata line if present
    ins_no: str = ""       # extracted from the Metadata line if present (ingredient chunks only)
    comparison_group: str = ""  # extracted from the Metadata line if present (tagged comparative-question pairs only)


# Matches a markdown heading of level 2 or 3: "## ..." or "### ..."
HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)

# Loosely matches doc_type: "value", entity: "value", ins_no: "value" inside
# the **Metadata:** `{...}` line — not a full JSON parser, just enough to
# pull the fields the baseline needs.
DOC_TYPE_RE = re.compile(r'doc_type:\s*"([^"]+)"')
ENTITY_RE = re.compile(r'entity:\s*"([^"]+)"')
INS_NO_RE = re.compile(r'ins_no:\s*"([^"]+)"')
COMPARISON_GROUP_RE = re.compile(r'comparison_group:\s*"([^"]+)"')


def parse_markdown_file(filepath: Path) -> list[Chunk]:
    text = filepath.read_text(encoding="utf-8")
    source_file = filepath.name

    matches = list(HEADING_RE.finditer(text))
    chunks: list[Chunk] = []

    # Some files declare doc_type once in a preamble line before the first
    # ##/### heading (e.g. ingredient_kb_tier2.md's file-level Metadata line)
    # rather than per-chunk. That preamble text is never itself a chunk, so
    # without this, every chunk in such a file would silently get
    # doc_type="" instead of the file's real doc_type. Used only as a
    # fallback default — a chunk's own Metadata line always wins.
    preamble = text[:matches[0].start()] if matches else text
    preamble_doc_type_match = DOC_TYPE_RE.search(preamble)
    default_doc_type = preamble_doc_type_match.group(1) if preamble_doc_type_match else ""

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk_text = text[start:end].strip()

        # Skip trivially small chunks (e.g. a stray header with no content) —
        # naive filter, not a smart one.
        if len(chunk_text) < 40:
            continue

        doc_type_match = DOC_TYPE_RE.search(chunk_text)
        entity_match = ENTITY_RE.search(chunk_text)
        ins_no_match = INS_NO_RE.search(chunk_text)
        comparison_group_match = COMPARISON_GROUP_RE.search(chunk_text)

        chunks.append(Chunk(
            chunk_id=f"{source_file}::chunk_{i:03d}",
            source_file=source_file,
            heading=heading,
            text=chunk_text,
            doc_type=doc_type_match.group(1) if doc_type_match else default_doc_type,
            entity=entity_match.group(1) if entity_match else "",
            ins_no=ins_no_match.group(1) if ins_no_match else "",
            comparison_group=comparison_group_match.group(1) if comparison_group_match else "",
        ))

    return chunks


def parse_all_kb_files(raw_dir: Path) -> list[Chunk]:
    """
    Parses the 4 markdown KB files (not products_compiled.json — that
    goes to SQLite via load_products.py, not the vector store).
    """
    kb_files = [
        "fssai_knowledge_base.md",
        "nutrition_knowledge_base.md",
        "ingredient_knowledge_base.md",
        "ingredient_kb_tier2.md",
    ]
    all_chunks: list[Chunk] = []
    for fname in kb_files:
        fpath = raw_dir / fname
        if not fpath.exists():
            print(f"WARNING: {fname} not found in {raw_dir}, skipping.")
            continue
        file_chunks = parse_markdown_file(fpath)
        print(f"{fname}: {len(file_chunks)} chunks")
        all_chunks.extend(file_chunks)
    return all_chunks


if __name__ == "__main__":
    # Quick manual check when run directly: python parse_kb.py <path to data/raw>
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
    chunks = parse_all_kb_files(raw_dir)
    print(f"\nTotal chunks: {len(chunks)}")
    print(f"\nSample chunk:\n{'-'*60}")
    print(chunks[10].chunk_id)
    print(f"doc_type={chunks[10].doc_type!r}  entity={chunks[10].entity!r}")
    print(chunks[10].text[:300])
