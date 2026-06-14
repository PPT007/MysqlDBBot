import logging
import os
import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

logger = logging.getLogger(__name__)

COLLECTION_NAME = "schema_embeddings"
VECTOR_SIZE = 384


class QdrantStoreError(Exception):
    """Base exception for Qdrant storage failures."""


def _get_qdrant_config() -> tuple[str, str]:
    qdrant_url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url:
        raise QdrantStoreError("QDRANT_URL environment variable is required.")
    if not api_key:
        raise QdrantStoreError("QDRANT_API_KEY environment variable is required.")

    return qdrant_url, api_key


def _get_client() -> QdrantClient:
    qdrant_url, api_key = _get_qdrant_config()
    try:
        client = QdrantClient(url=qdrant_url, api_key=api_key)
        logger.debug("Connected to Qdrant at %s", qdrant_url)
        return client
    except Exception as exc:
        raise QdrantStoreError("Failed to initialize Qdrant client.") from exc


def create_collection_if_not_exists() -> None:
    """Ensure the Qdrant collection exists with the correct vector configuration."""
    client = _get_client()

    try:
        if hasattr(client, "get_collections"):
            collections_response = client.get_collections()
            collection_names = [collection.name for collection in getattr(collections_response, "collections", [])]
            if COLLECTION_NAME in collection_names:
                logger.debug("Qdrant collection %s already exists.", COLLECTION_NAME)
                return

        if hasattr(client, "get_collection"):
            client.get_collection(collection_name=COLLECTION_NAME)
            logger.debug("Qdrant collection %s already exists.", COLLECTION_NAME)
            return
    except Exception:
        logger.info("Qdrant collection %s not found, creating it.", COLLECTION_NAME)

    try:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=rest.VectorParams(size=VECTOR_SIZE, distance=rest.Distance.COSINE),
        )
        logger.info(
            "Created Qdrant collection %s with vector size %d and cosine distance.",
            COLLECTION_NAME,
            VECTOR_SIZE,
        )
    except Exception as exc:
        print("\nREAL ERROR:")
        print(type(exc))
        print(exc)
        raise


def store_embeddings_in_qdrant(chunks: List[str], embeddings: List[List[float]]) -> None:
    """Upsert embeddings and chunk payloads into the Qdrant collection."""
    if len(chunks) != len(embeddings):
        raise QdrantStoreError("`chunks` and `embeddings` must have the same length.")

    if not chunks:
        logger.info("No chunks to store in Qdrant.")
        return

    create_collection_if_not_exists()
    client = _get_client()

    points: List[rest.PointStruct] = []
    for chunk_text, embedding in zip(chunks, embeddings):
        if len(embedding) != VECTOR_SIZE:
            raise QdrantStoreError(
                f"Embedding vectors must be length {VECTOR_SIZE}. Received length {len(embedding)}."
            )

        point = rest.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"chunk_text": chunk_text},
        )
        points.append(point)

    try:
        response = client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info("Upserted %d points into Qdrant collection %s.", len(points), COLLECTION_NAME)
        logger.debug("Qdrant upsert response: %s", response)
    except Exception as exc:
        raise QdrantStoreError("Failed to upsert points into Qdrant.") from exc


__all__ = [
    "create_collection_if_not_exists",
    "store_embeddings_in_qdrant",
    "QdrantStoreError",
]
