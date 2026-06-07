"""
Milestone 4b — Retrieval for The Unofficial Guide.

Pipeline stage 4:  Vector Store -> Retrieval
(Used by the generation step in Milestone 5.)

retrieve(query, k) embeds the query with the SAME model used at index time
(imported from embed.py), asks ChromaDB for the k nearest chunks by cosine
similarity, and returns them with their source metadata for attribution.

planning.md sets top-k = 5: enough context to answer most housing questions
without diluting the prompt with loosely-related chunks.

Run a quick manual test:
    python retrieve.py "Does MDC have student housing?"
    python retrieve.py "websites to find apartments near MDC" 5
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from embed import embed_texts, get_collection

# Tuned up from the planning.md default of 5 to 7: a borderline-but-correct
# chunk (e.g. the MDC FAQ "no housing" answer) was landing just outside the
# top-5 behind several listing-page chunks, so k=7 widens the safety margin.
DEFAULT_TOP_K = 7


@dataclass
class Result:
    """One retrieved chunk plus where it came from and how close it matched."""
    text: str
    source: str            # source document name (for attribution)
    chunk_index: int       # position within that document
    score: float           # cosine similarity in [0, 1]; higher = more relevant


def retrieve(query: str, k: int = DEFAULT_TOP_K) -> list[Result]:
    """Return the top-k chunks most relevant to `query`, best first."""
    if not query or not query.strip():
        return []

    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError(
            "The vector store is empty. Run `python embed.py` to build it first."
        )

    # Don't ask for more results than exist, or Chroma warns/clamps.
    k = max(1, min(k, collection.count()))

    query_embedding = embed_texts([query])[0]
    res = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma returns parallel lists nested one level per query; we sent one query.
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    results = []
    for text, meta, dist in zip(docs, metas, dists):
        # cosine distance = 1 - cosine similarity, so convert back to similarity.
        results.append(Result(
            text=text,
            source=meta.get("source", "unknown"),
            chunk_index=meta.get("chunk_index", -1),
            score=round(1.0 - dist, 4),
        ))
    return results


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print('Usage: python retrieve.py "your question" [k]')
        return
    # Trailing integer arg is treated as k.
    k = DEFAULT_TOP_K
    if len(args) > 1 and args[-1].isdigit():
        k = int(args[-1])
        args = args[:-1]
    query = " ".join(args)

    print(f"Query: {query!r}  (top-{k})\n")
    for rank, r in enumerate(retrieve(query, k), 1):
        snippet = r.text.replace("\n", " ")[:200]
        print(f"#{rank}  score={r.score:.3f}  [{r.source} #{r.chunk_index}]")
        print(f"    {snippet}\n")


if __name__ == "__main__":
    main()
