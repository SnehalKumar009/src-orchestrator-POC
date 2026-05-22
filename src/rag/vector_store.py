"""Qdrant vector store setup and operations."""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)
from src.config import QDRANT_HOST, QDRANT_PORT, RAG_COLLECTION_NAME, EMBEDDING_DIMENSION

# Lazy-load client
_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _client


def ensure_collection():
    """Create collection if it doesn't exist."""
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if RAG_COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=RAG_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created Qdrant collection: {RAG_COLLECTION_NAME}")


def add_documents(
    ids: list[str],
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
):
    """Add documents to the vector store."""
    ensure_collection()
    client = get_client()

    points = []
    for i, (doc_id, text, emb, meta) in enumerate(zip(ids, texts, embeddings, metadatas)):
        payload = {**meta, "text": text}
        points.append(PointStruct(id=i if not doc_id else hash(doc_id) % (2**63), vector=emb, payload=payload))

    client.upsert(collection_name=RAG_COLLECTION_NAME, points=points)


def query(
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
) -> dict:
    """
    Query the vector store for similar documents.

    Args:
        query_embedding: The query vector.
        n_results: Number of results to return.
        where: Optional metadata filter (e.g., {"category": "crypto"}).

    Returns:
        Dict with keys: ids, documents, metadatas, distances (each a list of lists).
    """
    ensure_collection()
    client = get_client()

    # Build Qdrant filter from where dict
    query_filter = None
    if where:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in where.items()
        ]
        query_filter = Filter(must=conditions)

    results = client.search(
        collection_name=RAG_COLLECTION_NAME,
        query_vector=query_embedding,
        limit=n_results,
        query_filter=query_filter,
    )

    # Format results to match expected interface
    result_ids = [str(r.id) for r in results]
    result_docs = [r.payload.get("text", "") for r in results]
    result_metas = [{k: v for k, v in r.payload.items() if k != "text"} for r in results]
    result_dists = [1.0 - r.score for r in results]  # cosine similarity → distance

    return {
        "ids": [result_ids],
        "documents": [result_docs],
        "metadatas": [result_metas],
        "distances": [result_dists],
    }


def get_stats() -> dict:
    """Get collection statistics."""
    ensure_collection()
    client = get_client()
    info = client.get_collection(RAG_COLLECTION_NAME)
    return {
        "name": RAG_COLLECTION_NAME,
        "count": info.points_count,
    }


def clear():
    """Delete and recreate the collection."""
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if RAG_COLLECTION_NAME in collections:
        client.delete_collection(RAG_COLLECTION_NAME)
    ensure_collection()
