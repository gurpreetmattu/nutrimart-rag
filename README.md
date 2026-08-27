# quick-commerce-rag (LangChain pipeline)

A LangChain-native RAG chatbot that answers questions about packaged food
products (ingredients, nutrition, allergens, FSSAI regulatory compliance)
for a mock quick-commerce app, with a React frontend. Hybrid retrieval
(BM25 + dense fusion), cross-encoder reranking, corrective retry, LLM
tool-calling for routing, SQL-grounded structured lookups, conversation
memory, and a numeric groundedness check.

This is the LangChain half of a larger portfolio project that also
includes hand-rolled (no-framework) pipelines as a comparison baseline —
this repo contains only the LangChain-native side.

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for a full deep dive: the data,
the request flow, hybrid retrieval, groundedness/consistency checking,
conversation memory, the LangChain integration itself, evaluation, and the
design decisions behind each piece (including what was tried and reverted).

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
- **`api/main.py`** — the app that actually serves the UI: FastAPI
  (`/api/*`) + the built React frontend (`frontend-react/dist`), on
  **port 8000**. Every `/api/chat` call goes through
  `ask_langchain_hybrid.py`.
- **`api/main_langchain.py`** — a second, API-only FastAPI app on
  **port 8001** fronting the exact same pipeline, with no frontend but
  extra observability fields (`tool_trace`, `timing`, `usage`) and an SSE
  `/api/chat/stream` endpoint.
- **`frontend-react/`** — the React (Vite) UI. Talks to whichever origin
  serves it via relative `/api/...` calls — no hardcoded port.

Two data stores:
1. **SQLite** (`db/products.sqlite`, built by `ingestion/load_products.py`)
   — deterministic per-product facts (ingredients, nutrition, allergens,
   FSSAI license). Fact-lookup questions bypass retrieval entirely via a
   deterministic router (`routing/query_router.py`).
2. **Qdrant** — chunks of the markdown knowledge base
   (`data/raw/*.md`), embedded with `BAAI/bge-small-en-v1.5`.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # or source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env         # fill in GROQ_API_KEY (+ HF_TOKEN)

docker-compose up -d         # starts Qdrant on localhost:6333

python src/ingestion/load_products.py data/raw db
python src/ingestion/embed_and_upsert.py data/raw

cd frontend-react
npm install
npm run build                # produces frontend-react/dist, served by api/main.py
```

## Run

```bash
# Full app: React UI + chat, port 8000
uvicorn api.main:app --reload --app-dir src --port 8000

# API-only, +observability, no frontend, port 8001
uvicorn api.main_langchain:app --reload --app-dir src --port 8001

# CLI, no server
python src/ask_langchain_hybrid.py "is aspartame safe in Diet Coke"
```

For frontend development with hot reload instead of the built `dist/`
bundle: `cd frontend-react && npm run dev` (proxies `/api` to
`http://127.0.0.1:8000`, see `vite.config.js`) while `api/main.py` runs
separately.

## Deploy (Google Cloud Run)

The `Dockerfile` builds the React frontend and the Python app into one
image; `products.sqlite` and both ML models (the bge embedder and the
cross-encoder reranker) are baked in at build time, so a cold start never
depends on Hugging Face Hub's availability/speed at runtime.

**Qdrant is not embedded in this image.** It's a separate, stateful
service — point the app at a managed instance rather than trying to run
Qdrant inside the same container:

1. Provision Qdrant somewhere reachable over HTTPS — [Qdrant Cloud's free
   tier](https://cloud.qdrant.io) is the simplest option.
2. **Before the app can answer anything**, run the ingestion step once
   against that instance — `python src/ingestion/embed_and_upsert.py
   data/raw` with `QDRANT_URL`/`QDRANT_API_KEY` set locally (pointing at
   the same instance). It recreates the whole collection each run, so it
   only needs to be run once (or again after a `data/raw/*.md` edit).

Then deploy the container:

1. Push this repo to GitHub (Cloud Run's "Continuously deploy from a
   repository" source builds straight from a connected repo via Cloud
   Build — no manual image push needed).
2. Cloud Run Console → **Create service** → connect the GitHub repo →
   Cloud Build auto-detects the `Dockerfile`.
3. **Region**: pick whichever is closest to your users (lower latency) —
   e.g. `asia-south1` (Mumbai) for India.
4. **Billing**: request-based works fine for a portfolio/demo project —
   you're only billed while a request is actually being handled, and
   min-instances=0 means it can scale to zero between requests.
5. **Container**: port `8080` (Cloud Run's `$PORT` — the `Dockerfile`'s
   `CMD` already reads `$PORT`, no change needed), **memory: 1 GiB**,
   **1 CPU**. 1 GiB is the number that matters most — see the note below.
6. **Environment variables**: paste every var from your `.env`
   (`GROQ_API_KEY*`, `HF_TOKEN`, `QDRANT_URL`, `QDRANT_API_KEY`, optional
   `LANGFUSE_*`) into the service's Variables tab — one name/value pair
   per row, the Console has no bulk `.env`-file paste.
7. **Execution environment**: Second generation (needed for the full
   Linux syscall surface `torch`/`sentence-transformers` use).
8. Deploy. Traffic auto-routes to the newest revision by default.

To deploy `api/main_langchain.py` (the no-frontend, +observability API) as
its own Cloud Run service from the same image/repo, override that
service's container start command to:
```
uvicorn api.main_langchain:app --host 0.0.0.0 --port $PORT --app-dir src
```

**Why 1 GiB memory, specifically:** this was hit as a real deploy failure,
not a guess. An earlier attempt on Render's free tier (512 MB) OOM-killed
(exit 137) on real queries that load both the embedding model and the
cross-encoder into memory at once — confirmed via Render's event log, and
reproduced/fixed locally with `docker run --memory=512m` before moving
platforms rather than just raising the limit blind. Cloud Run's 1 GiB tier
runs the same image with comfortable headroom; verified live post-deploy
with the same query class that broke the 512 MB tier (see the note below).

`products.sqlite` is baked into the image at build time, so every deploy
ships fresh product data with no separate migration step — only Qdrant's
content needs the manual one-time (or KB-edit-triggered) sync above.

## Eval

A hand-rolled RAGAS-equivalent harness (faithfulness, answer relevancy,
context precision/recall) against `ask_langchain_hybrid.py`:

```bash
python src/eval/run_ragas_eval.py --out ragas_report.md
python src/eval/run_ragas_eval.py --n 3   # cheap pilot
```

The same four metrics via the **real** `ragas` PyPI package (rotates across
every configured `GROQ_API_KEY*` — a real daily-quota exhaustion on a
single key is what a full 20-question run actually costs; see the script's
own docstring for the ragas/instructor version-compat bugs it works around):

```bash
python src/eval/run_real_ragas.py --out ragas_real_report.md
python src/eval/run_real_ragas.py --n 3            # cheap pilot
python src/eval/run_real_ragas.py --questions q01 q08 q27
```

Offline regression checks (no LLM/network cost):

```bash
python src/retrieval/test_search_hybrid.py
python src/generation/test_consistency.py
python src/api/test_security.py
python src/eval/test_ragas_metrics.py
```
