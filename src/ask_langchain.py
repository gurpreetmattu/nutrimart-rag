"""
ask_langchain.py — a third, standalone pipeline built with LangChain,
sitting alongside (not replacing) ask.py (Phase 3 naive baseline) and
ask_hybrid.py (Phase 5 hybrid pipeline). Neither of those is touched by
this file.

Scope, deliberately narrow: this mirrors ask.py's naive-retrieval shape
(dense top-k -> generation, no BM25/reranking/corrective retry) but wires
it with LangChain's own abstractions instead of the hand-rolled calls in
retrieval/search_baseline.py and generation/llm.py:
  - a custom langchain_core BaseRetriever (KBRetriever, below) over the
    SAME "kb_baseline" collection the other two pipelines already query —
    langchain_qdrant.QdrantVectorStore was tried first but assumes payload
    shaped {"page_content": ..., "metadata": {...}}, while this project's
    points store flat sibling fields; see KBRetriever's docstring
  - a custom langchain_core Embeddings adapter wrapping the same
    BAAI/bge-small-en-v1.5 model + BGE_QUERY_PREFIX (config.py) so results
    are directly comparable to search_baseline.py's — same model, same
    collection, same top_k
  - langchain_groq.ChatGroq for generation, chained via LCEL
    (retriever | prompt | llm | StrOutputParser), reusing this project's
    existing GROQ_API_KEY/GROQ_MODEL from generation/gateway.py
  - the same query_router.classify_query() + structured/product_facts.py
    SQL short-circuit ask.py and ask_hybrid.py both use, so product-fact
    questions still bypass retrieval/generation here too, kept for a fair
    routing comparison rather than re-deriving that logic a third time

Deliberately NOT ported: BM25 fusion, cross-encoder reranking, corrective
retry, groundedness checking, tool-calling agent routing, comparison_group
override — all of that is ask_hybrid.py-only by design (see
ask_langchain_hybrid.py, this repo's own full-parity port of it, if you
want that machinery in LangChain form). This file exists to demonstrate
the standard LangChain RAG pattern, not to replicate the hybrid pipeline's
engineering.

No fallback to Hugging Face on Groq quota exhaustion here (unlike
generation/gateway.py) — ChatGroq is used directly, since building a
LangChain-native fallback chain would be new scope beyond "build a
LangChain RAG pipeline." If Groq's daily quota is exhausted, this
pipeline will simply raise, same as calling Groq's SDK directly would.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

import os

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer

from config import BGE_QUERY_PREFIX, COLLECTION_NAME, EMBEDDING_MODEL, get_qdrant_client, get_sqlite_conn
from routing.query_router import classify_query
from structured.product_facts import answer_product_fact

# Same system prompt content as generation/llm.py's SYSTEM_PROMPT, trimmed
# to what a plain LCEL chain needs (no known_facts/structured_context
# sections — those are conversation-layer/tool-calling features that only
# ask_hybrid.py has).
SYSTEM_PROMPT = """You are a product-information assistant for a quick-commerce grocery app. \
You answer questions about packaged food products using ONLY the retrieved context provided \
below — you do not use outside knowledge about these specific products, ingredients, or \
regulations, even if you believe you know the answer.

Keep the answer SHORT: 4-5 sentences at the absolute most. Tag every non-trivial claim with \
[FACT] / [REGULATORY] / [INTERPRETATION] / [DERIVED CALCULATION] / [UNCERTAIN] at the start of \
the sentence, and cite the source after each tagged claim as (source_file.md, chunk/entry name), \
using only the filename and chunk/entry name from each context block's "[Source N: ...]" label \
(drop the "Source N:" part). If the retrieved context doesn't contain enough information, say so \
with [UNCERTAIN] rather than filling the gap from outside knowledge.

Retrieved context:
{context}"""


class BGEEmbeddings(Embeddings):
    """
    langchain_core.Embeddings adapter around the same SentenceTransformer
    model + query-prefix convention the other two pipelines use (see
    config.py's BGE_QUERY_PREFIX docstring — bge models need this prefix
    on queries only, never on documents). Wrapping it this way, instead of
    using langchain_huggingface's generic embeddings class, is what lets
    this pipeline read the SAME "kb_baseline" Qdrant collection the other
    two pipelines wrote (same model, same normalization, same absence of
    a prefix on the document side at ingestion time).
    """

    def __init__(self, model: SentenceTransformer):
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(BGE_QUERY_PREFIX + text, normalize_embeddings=True).tolist()


class KBRetriever(BaseRetriever):
    """
    langchain_core.retrievers.BaseRetriever over the "kb_baseline" Qdrant
    collection, querying it directly via qdrant_client (same as
    retrieval/search_baseline.py) rather than through langchain_qdrant's
    QdrantVectorStore wrapper. QdrantVectorStore's default document mapping
    expects payload shaped {"page_content": ..., "metadata": {...}} — this
    collection's points instead store flat sibling fields (source_file,
    heading, text, doc_type, ...), the schema every other pipeline in this
    project already reads. Rather than mutate the shared collection's
    payload shape to fit the wrapper (embed_and_upsert.py owns that shape
    and ask.py/ask_hybrid.py both depend on it), this retriever just maps
    the existing flat payload into Document objects directly — still a
    real LangChain BaseRetriever/Document, plugs into the LCEL chain the
    same way QdrantVectorStore's retriever would.
    """

    embeddings: Embeddings
    top_k: int = 5

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        client = get_qdrant_client()
        vector = self.embeddings.embed_query(query)
        results = client.query_points(
            collection_name=COLLECTION_NAME, query=vector, limit=self.top_k,
        ).points
        return [
            Document(
                page_content=r.payload["text"],
                metadata={
                    "score": r.score,
                    "chunk_id": r.payload["chunk_id"],
                    "source_file": r.payload["source_file"],
                    "heading": r.payload["heading"],
                    "doc_type": r.payload["doc_type"],
                },
            )
            for r in results
        ]


def format_docs(docs: list) -> str:
    parts = []
    for i, d in enumerate(docs, 1):
        source_file = d.metadata.get("source_file", "unknown")
        heading = d.metadata.get("heading", "unknown")
        parts.append(f"[Source {i}: {source_file}, {heading}]\n{d.page_content}")
    return "\n\n---\n\n".join(parts)


def build_chain(top_k: int = 5):
    """
    Standard LCEL RAG chain: retriever | prompt | llm | parser, built with
    {"context": retriever | format_docs, "question": passthrough} so the
    same retrieved docs are available for both the prompt and (if a caller
    wants them) inspection before generation.
    """
    embeddings = BGEEmbeddings(SentenceTransformer(EMBEDDING_MODEL))
    retriever = KBRetriever(embeddings=embeddings, top_k=top_k)

    llm = ChatGroq(
        model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
        api_key=os.environ["GROQ_API_KEY"],
        max_tokens=2048,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])

    chain = (
        {"context": retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever


def ask(query: str, top_k: int = 5, verbose: bool = True) -> str:
    sqlite_conn = get_sqlite_conn()
    route = classify_query(query, sqlite_conn)

    if route.route == "product_fact":
        if verbose:
            print(f"\nRouted to product_fact ({route.product_id}, field={route.fact_field})\n")
        answer = answer_product_fact(route.product_id, route.fact_field, sqlite_conn)
        sqlite_conn.close()
        return answer

    sqlite_conn.close()

    chain, retriever = build_chain(top_k=top_k)

    if verbose:
        docs = retriever.invoke(query)
        print(f"\nRetrieved {len(docs)} chunks:")
        for d in docs:
            print(f"  - {d.metadata.get('source_file')} — {d.metadata.get('heading')}")
        print()

    return chain.invoke(query)


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "is aspartame safe in Diet Coke"

    print(f"Query: {query}\n{'='*60}")
    answer = ask(query)
    print(f"Answer:\n{'-'*60}")
    print(answer)
