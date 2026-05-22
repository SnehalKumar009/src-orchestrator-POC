"""FastAPI REST server — exposes RAG query and DB endpoints to other containers."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.db.database import get_session
from src.db.models import Scan, SrcFinding, SrcRequirement
from src.db.seed import seed_database
from src.rag.ingest import ingest_mock_jira_fixes
from src.rag.query import query_rag
from src.rag.vector_store import get_stats, clear as clear_collection


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed DB and ingest RAG data on startup."""
    print("Starting up — seeding database...")
    seed_database()

    print("Starting up — ingesting RAG knowledge base...")
    ingest_mock_jira_fixes()

    stats = get_stats()
    print(f"Ready. RAG collection '{stats['name']}' has {stats['count']} documents.")
    yield
    print("Shutting down.")


app = FastAPI(
    title="SRC Orchestrator API",
    description="REST API for RAG queries and compliance findings",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Request / Response Models ─────────────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    req_id: str = Field(default="", description="Requirement ID, e.g. SEC-509-CERT-2")
    component: str = Field(default="", description="Component path, e.g. ccm/Projects/CAPF")
    category: str = Field(default="", description="Category: crypto, auth, hardening, network, logging, deprecation")
    top_k: int = Field(default=5, description="Number of results to return")
    use_metadata_filter: bool = Field(default=True, description="Filter by category for precise results")


class RAGResult(BaseModel):
    text: str
    source: str
    req_id: str
    component: str
    category: str
    fix_type: str
    jira_key: str
    chunk_type: str
    distance: float | None


class FindingSummary(BaseModel):
    id: int
    component: str
    req_id: str
    status: str
    fix_status: str
    category: str | None
    routed_agent: str | None
    ai_score: float | None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check — confirms API, DB, and Qdrant are reachable."""
    session = get_session()
    try:
        scan_count = session.query(Scan).count()
    finally:
        session.close()

    rag_stats = get_stats()
    return {
        "status": "healthy",
        "db_scans": scan_count,
        "rag_collection": rag_stats["name"],
        "rag_documents": rag_stats["count"],
    }


@app.post("/query", response_model=list[RAGResult])
def rag_query(request: RAGQueryRequest):
    """
    Query the RAG knowledge base for similar past fixes.

    This is the endpoint other containers / agents will call.
    """
    results = query_rag(
        req_id=request.req_id,
        component=request.component,
        category=request.category,
        top_k=request.top_k,
        use_metadata_filter=request.use_metadata_filter,
    )
    return results


@app.get("/findings", response_model=list[FindingSummary])
def get_findings():
    """Get all current compliance findings from the database."""
    session = get_session()
    try:
        findings = session.query(SrcFinding).all()
        result = []
        for f in findings:
            req = session.get(SrcRequirement, f.requirement_id)
            result.append(FindingSummary(
                id=f.id,
                component=f.component,
                req_id=req.req_id if req else "",
                status=f.status.value if hasattr(f.status, "value") else str(f.status),
                fix_status=f.fix_status.value if hasattr(f.fix_status, "value") else str(f.fix_status),
                category=f.category,
                routed_agent=f.routed_agent,
                ai_score=f.ai_score,
            ))
        return result
    finally:
        session.close()


@app.get("/findings/{finding_id}")
def get_finding_with_suggestions(finding_id: int):
    """Get a specific finding + auto-query RAG for fix suggestions."""
    session = get_session()
    try:
        finding = session.get(SrcFinding, finding_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")

        req = session.get(SrcRequirement, finding.requirement_id)

        # Auto-query RAG for this finding
        suggestions = query_rag(
            req_id=req.req_id if req else "",
            component=finding.component,
            category=finding.category or "",
            top_k=3,
        )

        return {
            "finding": {
                "id": finding.id,
                "component": finding.component,
                "req_id": req.req_id if req else "",
                "status": finding.status.value if hasattr(finding.status, "value") else str(finding.status),
                "reason": finding.reason,
                "fix_steps": finding.fix_steps,
                "category": finding.category,
                "routed_agent": finding.routed_agent,
                "ai_score": finding.ai_score,
            },
            "rag_suggestions": suggestions,
        }
    finally:
        session.close()


@app.get("/rag/stats")
def rag_stats():
    """Get RAG collection statistics."""
    return get_stats()


@app.post("/rag/reingest")
def rag_reingest():
    """Clear and re-ingest the RAG knowledge base."""
    clear_collection()
    ingest_mock_jira_fixes()
    return get_stats()
