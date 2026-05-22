"""
End-to-end demo: DB setup + RAG ingestion + RAG query.

Usage:
    python -m demo
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("=" * 80)
    print("SRC Orchestrator — RAG POC Demo")
    print("=" * 80)

    # ── Step 1: Seed data (tables already created by PostgreSQL init script)
    print("\n[1/4] Seeding sample data into database...")
    from src.db.seed import seed_database
    seed_database()

    # ── Step 2: Show DB stats ──────────────────────────────────────────────
    print("\n[2/4] Database contents:")
    from src.db.database import get_session
    from src.db.models import Scan, SrcFinding, SrcRequirement
    session = get_session()
    scan_count = session.query(Scan).count()
    finding_count = session.query(SrcFinding).count()
    req_count = session.query(SrcRequirement).count()
    print(f"  Scans:        {scan_count}")
    print(f"  Requirements: {req_count}")
    print(f"  Findings:     {finding_count}")

    # Show findings summary
    findings = session.query(SrcFinding).all()
    print(f"\n  {'Component':<30} {'Req ID':<20} {'Status':<18} {'Agent':<20} {'AI Score'}")
    print(f"  {'-'*30} {'-'*20} {'-'*18} {'-'*20} {'-'*8}")
    for f in findings:
        req = session.get(SrcRequirement, f.requirement_id)
        print(f"  {f.component:<30} {req.req_id:<20} {f.status:<18} {f.routed_agent or 'N/A':<20} {f.ai_score or 0:.0f}")
    session.close()

    # ── Step 3: Ingest mock fixes into RAG ─────────────────────────────────
    print("\n[3/4] Ingesting mock Jira fixes into RAG knowledge base...")
    from src.rag.ingest import ingest_mock_jira_fixes
    ingest_mock_jira_fixes()

    # ── Step 4: Query RAG ──────────────────────────────────────────────────
    print("\n[4/4] Running sample RAG queries...\n")
    from src.rag.query import query_rag, print_results

    # Query 1: Crypto agent looking for cert validation fixes
    print("QUERY 1: Crypto agent needs help fixing SEC-509-CERT-2 on CAPF")
    results = query_rag(
        req_id="SEC-509-CERT-2",
        component="ccm/Projects/CAPF",
        category="crypto",
    )
    print_results(results)

    # Query 2: Hardening agent looking for SSH hardening
    print("\n\nQUERY 2: Hardening agent needs help with SSH config")
    results = query_rag(
        req_id="SEC-HRD-SSH-1",
        component="ccm/Projects/CAPF",
        category="hardening",
    )
    print_results(results)

    # Query 3: Deprecation agent looking for library upgrade
    print("\n\nQUERY 3: Deprecation agent needs help with log4j upgrade")
    results = query_rag(
        req_id="SEC-DEP-LIB-1",
        component="cup/Projects/XCP",
        category="deprecation",
    )
    print_results(results)

    # Query 4: Cross-category search (no filter)
    print("\n\nQUERY 4: Broad search — 'bind address 0.0.0.0 network hardening'")
    results = query_rag(
        req_id="SEC-NET-PORT-1",
        category="network",
    )
    print_results(results)

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
