"""RAG query interface — the function agents will call to get similar past fixes."""

from src.rag.embedder import embed_single
from src.rag.vector_store import query as vector_query
from src.config import RAG_TOP_K


def query_rag(
    req_id: str = "",
    component: str = "",
    category: str = "",
    top_k: int = RAG_TOP_K,
    use_metadata_filter: bool = True,
) -> list[dict]:
    """
    Query the RAG knowledge base for similar past fixes.

    This is the main interface that specialist fix agents call.

    Args:
        req_id: Requirement ID (e.g., "SEC-509-CERT-2").
        component: Component path (e.g., "ccm/Projects/CAPF").
        category: Fix category (e.g., "crypto", "auth", "hardening").
        top_k: Number of results to return.
        use_metadata_filter: If True, filter by category for more precise results.

    Returns:
        List of dicts with keys: text, source, req_id, component, category,
        fix_type, jira_key, distance.
    """
    # Build query text from available context
    query_parts = []
    if req_id:
        query_parts.append(f"Requirement: {req_id}")
    if component:
        query_parts.append(f"Component: {component}")
    if category:
        query_parts.append(f"Category: {category}")

    query_text = " | ".join(query_parts) if query_parts else "security compliance fix"

    # Embed the query
    query_embedding = embed_single(query_text)

    # Build metadata filter
    where_filter = None
    if use_metadata_filter and category:
        where_filter = {"category": category}

    # Query vector store
    results = vector_query(
        query_embedding=query_embedding,
        n_results=top_k,
        where=where_filter,
    )

    # Format results
    formatted = []
    if results and results.get("documents") and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else None

            formatted.append({
                "text": doc,
                "source": meta.get("source", ""),
                "req_id": meta.get("req_id", ""),
                "component": meta.get("component", ""),
                "category": meta.get("category", ""),
                "fix_type": meta.get("fix_type", ""),
                "jira_key": meta.get("jira_key", ""),
                "chunk_type": meta.get("chunk_type", ""),
                "distance": distance,
            })

    return formatted


def print_results(results: list[dict]):
    """Pretty-print RAG query results."""
    if not results:
        print("No results found.")
        return

    print(f"\n{'='*80}")
    print(f"Found {len(results)} similar past fixes:")
    print(f"{'='*80}")

    for i, r in enumerate(results, 1):
        print(f"\n--- Result {i} (distance: {r['distance']:.4f}) ---")
        print(f"  Jira:      {r['jira_key']}")
        print(f"  Req ID:    {r['req_id']}")
        print(f"  Component: {r['component']}")
        print(f"  Category:  {r['category']}")
        print(f"  Fix Type:  {r['fix_type']}")
        print(f"  Chunk:     {r['chunk_type']}")
        print(f"  Text:      {r['text'][:200].encode('ascii', 'replace').decode()}...")
