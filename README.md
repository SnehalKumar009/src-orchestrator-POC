# SRC Resolution Orchestrator

Security Requirements Compliance (SRC) orchestrator with a RAG-powered knowledge base for intelligent fix recommendations. Runs as 3 Docker containers with a REST API.

## Architecture

```
┌──────────────┐         ┌───────────────────┐
│ Agent / curl  │──POST──▶│ src-orchestrator   │
│               │◀──JSON──│ FastAPI :8000      │
└──────────────┘         └──┬──────────┬──────┘
                            │          │
                     ┌──────▼──┐  ┌────▼────┐
                     │PostgreSQL│  │ Qdrant  │
                     │  :5432   │  │  :6333  │
                     └─────────┘  └─────────┘
```

## Quick Start

```bash
# Build and run all 3 containers
docker compose up --build

# Verify
curl http://localhost:8000/health
```

Swagger docs at: **http://localhost:8000/docs**

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health check (DB + Qdrant status) |
| `POST` | `/query` | RAG query — returns similar past fixes |
| `GET` | `/findings` | List all compliance findings |
| `GET` | `/findings/{id}` | Get finding + auto-suggested RAG fixes |
| `GET` | `/rag/stats` | Qdrant collection statistics |
| `POST` | `/rag/reingest` | Clear and re-ingest RAG data |

### Example: RAG Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"req_id": "SEC-509-CERT-2", "category": "crypto", "top_k": 3}'
```

## Project Structure

```
src-orchestrator/
├── src/
│   ├── config.py              # Central configuration
│   ├── api/
│   │   └── app.py             # FastAPI REST server
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine + session (PostgreSQL)
│   │   ├── models.py          # All 6 DB tables
│   │   └── seed.py            # Sample data
│   └── rag/
│       ├── embedder.py        # Chunking + embedding (sentence-transformers)
│       ├── vector_store.py    # Qdrant operations
│       ├── ingest.py          # Ingestion pipeline (mock Jira data)
│       └── query.py           # query_rag() interface
├── db/
│   └── init/
│       └── 01_create_tables.sql  # PostgreSQL schema (runs on first start)
├── demo.py                    # Standalone end-to-end test script
├── Dockerfile                 # App container
├── docker-compose.yml         # 3-container orchestration
├── requirements.txt
├── .env
└── README.md
```

## DB Tables (PostgreSQL)

| Table | Purpose |
|---|---|
| `scans` | Weekly scan metadata |
| `src_findings` | Per-component compliance findings |
| `src_requirements` | PSB requirement definitions |
| `fix_history` | Fix attempt audit trail |
| `report_updates` | Report regeneration tracking |
| `scan_reports` | Raw HTML/JSON reports |

## RAG Pipeline (Qdrant)

**Ingest:** Mock Jira fixes → chunk (description + comments + diffs) → embed (all-MiniLM-L6-v2) → store (Qdrant)

**Query:** `POST /query` → embed query → vector search in Qdrant → return top-K similar past fixes

## Tech Stack

- **Python 3.12** + **FastAPI** + **Uvicorn**
- **PostgreSQL 16** — relational database (Docker container)
- **Qdrant** — vector database for RAG (Docker container)
- **SQLAlchemy 2.x** — ORM
- **sentence-transformers** — local embeddings (`all-MiniLM-L6-v2`)
- **Docker Compose** — container orchestration
