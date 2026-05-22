# SRC Resolution Orchestrator

Security Requirements Compliance (SRC) orchestrator with a RAG-powered knowledge base for intelligent fix recommendations.

## Architecture

```
┌─────────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  src-orchestrator    │    │   PostgreSQL 16  │    │    Qdrant       │
│  (App Container)     │───▶│  (DB Container)  │    │ (RAG Container) │
│                      │    │   Port 5432      │    │  Port 6333      │
│                      │───▶│                  │    │                 │
└─────────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start (Docker)

```bash
# Build and run all 3 containers
docker compose up --build

# Run only infrastructure (DB + Qdrant)
docker compose up postgres qdrant -d

# Run demo against running infrastructure
docker compose run --rm app
```

## Quick Start (Local Development)

```bash
# 1. Start infrastructure
docker compose up postgres qdrant -d

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the demo
python -m demo
```

## Project Structure

```
src-orchestrator/
├── src/
│   ├── config.py              # Central configuration
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine + session (PostgreSQL)
│   │   ├── models.py          # All 6 DB tables
│   │   └── seed.py            # Sample data
│   └── rag/
│       ├── embedder.py        # Chunking + embedding (sentence-transformers)
│       ├── vector_store.py    # Qdrant operations
│       ├── ingest.py          # Ingestion pipeline (mock Jira data)
│       └── query.py           # query_rag() interface
├── demo.py                    # End-to-end demo
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

**Query:** `query_rag(req_id, component, category)` → returns top-K similar past fixes

## Tech Stack

- **Python 3.12**
- **PostgreSQL 16** — relational database (Docker container)
- **Qdrant** — vector database for RAG (Docker container)
- **SQLAlchemy 2.x** — ORM
- **sentence-transformers** — local embeddings (`all-MiniLM-L6-v2`)
- **Docker Compose** — container orchestration
