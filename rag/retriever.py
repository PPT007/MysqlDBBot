import json
import sys
from math import sqrt
from pathlib import Path
from typing import Any, Dict, List

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from rag.embedder import embed_texts
from rag.qdrant_store import search_similar_chunks

EMBEDDINGS_PATH = Path(__file__).resolve().parent / "embeddings" / "schema_embeddings.json"


def load_chunk_embeddings(path: Path) -> List[Dict[str, Any]]:
    """Load chunk metadata and embeddings from a JSON file."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    # Expect a top-level object with a `chunks` array.
    return payload.get("chunks", [])


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """Compute cosine similarity between two vectors using pure Python."""
    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for a, b in zip(vector_a, vector_b):
        dot_product += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (sqrt(norm_a) * sqrt(norm_b))


def score_chunks(question: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Embed the question and compare it with each chunk embedding."""
    question_embedding = embed_texts([question])[0]

    scored_chunks = []
    for chunk in chunks:
        chunk_embedding = chunk.get("embedding", [])
        similarity = cosine_similarity(question_embedding, chunk_embedding)
        scored_chunks.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "text": chunk.get("text"),
                "similarity": similarity,
            }
        )

    return scored_chunks


def get_top_chunks(question: str, top_n: int = 3) -> List[Dict[str, Any]]:
    """Return the top N chunks ranked by similarity to the question."""
    try:
        question_embedding = embed_texts([question])[0]
        return search_similar_chunks(question_embedding, top_n=top_n)
    except Exception as exc:
        print(f"\n[Warning] Qdrant search failed: {exc}. Falling back to local JSON schema search...\n")
        chunks = load_chunk_embeddings(EMBEDDINGS_PATH)
        scored_chunks = score_chunks(question, chunks)
        scored_chunks.sort(key=lambda item: item["similarity"], reverse=True)
        return scored_chunks[:top_n]


def get_display_name(chunk_text: str) -> str:
    """Return a short name for the chunk for human terminal output.

    Use only the first line of the chunk text so column definitions and other
    multi-line details are never included in the terminal display name.
    """
    first_line = chunk_text.strip().splitlines()[0].strip()

    if first_line.startswith("Table:"):
        # Preserve just the table name and ignore any later lines or columns.
        return first_line.split("Table:", 1)[1].strip()

    if first_line.startswith("==========") and first_line.endswith("=========="):
        # Normalize schema section headers like relationship blocks.
        return first_line.strip("=").strip().lower()

    # Fallback: use the trimmed first line, without the full chunk body.
    return first_line


def display_top_chunks(question: str, chunks: List[Dict[str, Any]]) -> None:
    """Print a human-friendly summary without exposing full chunk text.

    The terminal output is for human debugging only. The full chunk text is preserved
    in the returned chunk objects for future LLM prompt-building stages.
    """
    print("Top Matching Chunks:\n")

    for index, chunk in enumerate(chunks, start=1):
        display_name = get_display_name(chunk["text"])
        print(f"{index}. {display_name:<15} {chunk['similarity']:.3f}")


def main() -> None:
    """Direct execution entry point for manual testing of retrieval."""
    question = input("Enter a question about the schema: ").strip()
    if not question:
        print("No question provided.")
        return

    top_chunks = get_top_chunks(question, top_n=3)
    display_top_chunks(question, top_chunks)


if __name__ == "__main__":
    main()
