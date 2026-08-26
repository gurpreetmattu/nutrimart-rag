# quick-commerce-rag (LangChain pipeline)

A LangChain-native RAG pipeline that answers questions about packaged food
products (ingredients, nutrition, allergens, FSSAI regulatory compliance)
for a mock quick-commerce app. Hybrid retrieval (BM25 + dense fusion),
cross-encoder reranking, corrective retry, LLM tool-calling for
routing, SQL-grounded structured lookups, conversation memory, and a
numeric groundedness check.

This is the LangChain half of a larger portfolio project that also
includes hand-rolled (no-framework) pipelines as a comparison baseline —
this repo contains only the LangChain-native side.

## Architecture

- **`ask_langchain.py`** — a naive pipeline: dense-only retrieval via a
  custom `langchain_core.BaseRetriever`, no reranking/retry.
- **`ask_langchain_hybrid.py`** — the full pipeline: BM25+dense fusion,
  cross-encoder reranking, corrective query-rewrite retry, an LLM
  tool-calling router (`agent/tools.py`) that dispatches between SQL
  lookups and knowledge-base retrieval, conversation state/follow-up
  resolution, and a post-generation groundedness check. Its own
  `groq_gateway_invoke()` reimplements multi-key rotation + a proactive
  per-key daily token-budget ledger + a Hugging Face fallback, all
  LangChain-native (`ChatGroq`/`ChatHuggingFace`).
- **`hybrid_core.py`** — the retrieval-decision logic shared by the hybrid
  pipeline (corrective retry, BM25-consensus check, the regex safety-nets
  that force a knowledge-base search for evaluative/regulatory questions,
  the agent system prompt).
- **`api/main_langchain.py`** — FastAPI app fronting `ask_langchain_hybrid.py`
  (models preloaded once at startup), with `/api/chat` and an SSE
  `/api/chat/stream`.

Two data stores:
1. **SQLite** (`db/products.sqlite`, built by `ingestion/load_products.py`)
   — deterministic per-product facts (ingredients, nutrition, allergens,
   FSSAI license). Fact-lookup questions bypass retrieval entirely via a
   deterministic router (`routing/query_router.py`).
2. **Qdrant** — chunks of the markdown knowledge base
   (`data/raw/*.md`), embedded with `BAAI/bge-small-en-v1.5`.

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # or source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env         # fill in GROQ_API_KEY (+ HF_TOKEN)

docker-compose up -d         # starts Qdrant

python src/ingestion/load_products.py data/raw db
python src/ingestion/embed_and_upsert.py data/raw
```

## Run

```bash
python src/ask_langchain_hybrid.py "is aspartame safe in Diet Coke"

uvicorn api.main_langchain:app --reload --app-dir src --port 8001
```

## Eval

A hand-rolled RAGAS-equivalent harness (faithfulness, answer relevancy,
context precision/recall) against `ask_langchain_hybrid.py`:

```bash
python src/eval/run_ragas_eval.py --out ragas_report.md
python src/eval/run_ragas_eval.py --n 3   # cheap pilot
```

Offline regression checks (no LLM/network cost):

```bash
python src/retrieval/test_search_hybrid.py
python src/generation/test_consistency.py
python src/api/test_security.py
python src/eval/test_ragas_metrics.py
```
