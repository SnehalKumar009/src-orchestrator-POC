"""Embedding and chunking utilities for the RAG pipeline."""

from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL

# Lazy-load model
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("Model loaded.")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into vectors."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_single(text: str) -> list[float]:
    """Embed a single text into a vector."""
    return embed_texts([text])[0]


def chunk_jira_fix(fix_data: dict) -> list[dict]:
    """
    Chunk a Jira fix record into RAG-ready documents.

    Strategy: description as one chunk + each comment as a separate chunk.
    Each chunk carries metadata for filtered retrieval.
    """
    chunks = []
    base_metadata = {
        "source": "jira",
        "req_id": fix_data.get("req_id", ""),
        "component": fix_data.get("component", ""),
        "category": fix_data.get("category", ""),
        "fix_type": fix_data.get("fix_type", "code"),
        "jira_key": fix_data.get("jira_key", ""),
    }

    # Chunk 1: Description (the main fix description)
    if fix_data.get("description"):
        chunks.append({
            "text": f"[Fix for {fix_data.get('req_id', 'unknown')}] {fix_data['description']}",
            "metadata": {**base_metadata, "chunk_type": "description"},
        })

    # Chunk 2+: Individual comments (discussions, code snippets)
    for i, comment in enumerate(fix_data.get("comments", [])):
        if comment.strip():
            chunks.append({
                "text": f"[Comment on {fix_data.get('req_id', 'unknown')}] {comment}",
                "metadata": {**base_metadata, "chunk_type": "comment", "comment_index": str(i)},
            })

    # Chunk: Code diff if available
    if fix_data.get("code_diff"):
        chunks.append({
            "text": f"[Code diff for {fix_data.get('req_id', 'unknown')}] {fix_data['code_diff']}",
            "metadata": {**base_metadata, "chunk_type": "code_diff"},
        })

    return chunks
