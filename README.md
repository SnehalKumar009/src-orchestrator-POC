# SRC Resolution Orchestrator — RAG POC

Security Requirements Compliance (SRC) orchestrator with a RAG-powered knowledge base for intelligent fix recommendations.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the demo
python -m demo
```

## Project Structure

```
src-orchestrator/
├── src/
│   ├── config.py              # Central configuration
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine + session
│   │   ├── models.py          # All 6 DB tables
│   │   └── seed.py            # Sample data
│   └── rag/
│       ├── embedder.py        # Chunking + embedding
│       ├── vector_store.py    # ChromaDB operations
│       ├── ingest.py          # Ingestion pipeline (mock Jira data)
│       └── query.py           # query_rag() interface
├── data/                      # Auto-created: SQLite DB + ChromaDB
├── demo.py                    # End-to-end demo
├── requirements.txt
├── .env
└── README.md
```

## DB Tables

| Table | Purpose |
|---|---|
| `scans` | Weekly scan metadata |
| `src_findings` | Per-component compliance findings |
| `src_requirements` | PSB requirement definitions |
| `fix_history` | Fix attempt audit trail |
| `report_updates` | Report regeneration tracking |
| `scan_reports` | Raw HTML/JSON reports |

## RAG Pipeline

**Ingest:** Mock Jira fixes → chunk (description + comments + diffs) → embed (all-MiniLM-L6-v2) → store (ChromaDB)

**Query:** `query_rag(req_id, component, category)` → returns top-K similar past fixes

## Tech Stack (POC)

- **Python 3.11+**
- **SQLAlchemy 2.x** (SQLite for POC, PostgreSQL for prod)
- **ChromaDB** (local vector DB, swap to Qdrant for prod)
- **sentence-transformers** (local embeddings, swap to text-embedding-3-small for prod)
