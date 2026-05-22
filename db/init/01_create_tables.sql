-- SRC Orchestrator — Database Schema
-- Runs automatically on first PostgreSQL container startup

-- ── Enum Types ────────────────────────────────────────────────────────────────

CREATE TYPE compliancestatus AS ENUM ('COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'NOT_APPLICABLE');
CREATE TYPE fixstatus AS ENUM ('pending', 'fixed', 'dismissed');
CREATE TYPE deltatype AS ENUM ('NEW', 'CHANGED', 'UNCHANGED');

-- ── Tables ────────────────────────────────────────────────────────────────────

CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    week INTEGER NOT NULL,
    year INTEGER NOT NULL,
    csdl_id VARCHAR(50) NOT NULL,
    scan_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    total_findings INTEGER DEFAULT 0,
    non_compliant_count INTEGER DEFAULT 0,
    partial_count INTEGER DEFAULT 0,
    compliant_count INTEGER DEFAULT 0,
    summary TEXT
);

CREATE INDEX ix_scans_week_year ON scans (week, year);


CREATE TABLE src_requirements (
    id SERIAL PRIMARY KEY,
    req_id VARCHAR(50) UNIQUE NOT NULL,
    psb_text TEXT NOT NULL,
    section VARCHAR(100),
    category VARCHAR(50),
    tags TEXT,
    priority VARCHAR(10)
);

CREATE INDEX ix_src_req_category ON src_requirements (category);


CREATE TABLE src_findings (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER NOT NULL REFERENCES scans(id),
    requirement_id INTEGER NOT NULL REFERENCES src_requirements(id),
    component VARCHAR(200) NOT NULL,
    status compliancestatus DEFAULT 'NON_COMPLIANT',
    reason TEXT,
    fix_steps TEXT,
    category VARCHAR(50),
    risk_area VARCHAR(50),
    delta_type deltatype DEFAULT 'UNCHANGED',
    routed_agent VARCHAR(50),
    fix_status fixstatus DEFAULT 'pending',
    fixed_by VARCHAR(100),
    fixed_at TIMESTAMP,
    pr_url VARCHAR(500),
    ai_score FLOAT
);

CREATE INDEX ix_findings_component ON src_findings (component);
CREATE INDEX ix_findings_status ON src_findings (status);
CREATE INDEX ix_findings_fix_status ON src_findings (fix_status);
CREATE INDEX ix_findings_category ON src_findings (category);


CREATE TABLE fix_history (
    id SERIAL PRIMARY KEY,
    finding_id INTEGER NOT NULL REFERENCES src_findings(id),
    attempt_number INTEGER DEFAULT 1,
    agent_name VARCHAR(50),
    diff TEXT,
    test_result VARCHAR(20),
    pr_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC')
);


CREATE TABLE report_updates (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER NOT NULL REFERENCES scans(id),
    regenerated_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    trigger VARCHAR(50),
    changes_summary TEXT
);


CREATE TABLE scan_reports (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER NOT NULL REFERENCES scans(id),
    report_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC')
);
