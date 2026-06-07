"""
Milestone 4a — Embedding + vector store for The Unofficial Guide.

Pipeline stage 3:  Chunking -> Embedding + Vector Store
(Reads documents/chunks.json produced by documents/ingest.py.)

This implements the planning.md "Retrieval Approach" section:
    Embedding model : all-MiniLM-L6-v2 (sentence-transformers, runs locally,
                      no API key, no rate limits)
    Vector store    : ChromaDB, persisted on disk at ./chroma_db
    Metadata        : each chunk stored with its source document name and its
                      position (chunk_index) within that document — needed for
                      source attribution in the generation step (Milestone 5).

Run:
    python embed.py            # build/refresh the index from chunks.json
    python embed.py --peek     # print collection size + one stored record

The model + collection helpers here are imported by retrieve.py so indexing and
querying always use the SAME embedding model (mismatched models = garbage
similarity scores).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb

# --- Configuration -----------------------------------------------------------

MODEL_NAME = "all-MiniLM-L6-v2"
ROOT = Path(__file__).resolve().parent
CHUNKS_FILE = ROOT / "documents" / "chunks.json"
CHROMA_DIR = ROOT / "chroma_db"          # gitignored; persistent on-disk store
COLLECTION_NAME = "mdc_housing"

# Loading the model takes a few seconds, so cache it across calls in one process.
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load (once) and return the embedding model.

    SentenceTransformer("all-MiniLM-L6-v2") downloads the model the first time
    (~90 MB) and caches it under ~/.cache; later calls are instant and offline.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Encode a list of strings into embedding vectors.

    normalize_embeddings=True makes every vector unit length, which is what the
    cosine distance space (set on the collection below) expects.
    """
    vectors = get_model().encode(
        texts, normalize_embeddings=True, show_progress_bar=len(texts) > 64
    )
    return vectors.tolist()


def get_collection(reset: bool = False) -> "chromadb.api.models.Collection.Collection":
    """Open (or create) the persistent ChromaDB collection.

    - PersistentClient writes the index to CHROMA_DIR so it survives between
      runs (an in-memory Client would vanish when the process exits).
    - metadata={"hnsw:space": "cosine"} tells Chroma to rank by cosine
      similarity, the right metric for normalized MiniLM embeddings. (The
      default is L2/Euclidean.)
    - reset=True drops any existing collection first. Used by build_index so a
      rebuild exactly mirrors chunks.json — otherwise chunks that disappeared
      after a re-ingest (when chunk counts shift) would linger as stale records.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet — nothing to drop
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


# --- Index build -------------------------------------------------------------

def load_chunks() -> list[dict]:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"{CHUNKS_FILE} not found. Run `python documents/ingest.py` first."
        )
    return json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))


def build_index() -> int:
    """Embed every chunk and upsert it into ChromaDB with source metadata.

    Uses upsert (not add) keyed on each chunk's stable `id` so re-running after
    a re-ingest updates existing records instead of erroring on duplicates.
    Returns the number of chunks indexed.
    """
    chunks = load_chunks()
    if not chunks:
        print("No chunks to index — chunks.json is empty.")
        return 0

    # Fresh collection so the index mirrors chunks.json exactly (no stale ids).
    collection = get_collection(reset=True)

    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]}
                 for c in chunks]

    print(f"Embedding {len(chunks)} chunks with {MODEL_NAME} ...")
    embeddings = embed_texts(documents)

    print(f"Adding to ChromaDB collection '{COLLECTION_NAME}' ...")
    collection.add(
        ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
    )

    total = collection.count()
    print(f"Done. Collection now holds {total} chunks at {CHROMA_DIR}")
    return total


def peek() -> None:
    """Print collection size and one stored record to confirm metadata stuck."""
    collection = get_collection()
    print(f"Collection '{COLLECTION_NAME}': {collection.count()} chunks")
    sample = collection.get(limit=1, include=["documents", "metadatas"])
    if sample["ids"]:
        print("Sample id:      ", sample["ids"][0])
        print("Sample metadata:", sample["metadatas"][0])
        print("Sample text:    ", sample["documents"][0][:160], "...")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--peek":
        peek()
        return
    build_index()


if __name__ == "__main__":
    main()
