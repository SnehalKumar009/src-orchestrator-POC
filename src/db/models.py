from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Integer, Float, DateTime, ForeignKey, Index, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.database import Base
import enum


# ── Enums ──────────────────────────────────────────────────────────────────────

class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FixStatus(str, enum.Enum):
    PENDING = "pending"
    FIXED = "fixed"
    DISMISSED = "dismissed"


class DeltaType(str, enum.Enum):
    NEW = "NEW"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"


# ── Models ─────────────────────────────────────────────────────────────────────

class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    csdl_id: Mapped[str] = mapped_column(String(50), nullable=False)
    scan_date: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    non_compliant_count: Mapped[int] = mapped_column(Integer, default=0)
    partial_count: Mapped[int] = mapped_column(Integer, default=0)
    compliant_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    findings: Mapped[list["SrcFinding"]] = relationship(back_populates="scan")
    reports: Mapped[list["ScanReport"]] = relationship(back_populates="scan")

    __table_args__ = (
        Index("ix_scans_week_year", "week", "year"),
    )


class SrcRequirement(Base):
    __tablename__ = "src_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    req_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    psb_text: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array as text
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)  # P10, P20, etc.

    # Relationships
    findings: Mapped[list["SrcFinding"]] = relationship(back_populates="requirement")

    __table_args__ = (
        Index("ix_src_req_category", "category"),
    )


class SrcFinding(Base):
    __tablename__ = "src_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), nullable=False)
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("src_requirements.id"), nullable=False
    )
    component: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(ComplianceStatus, values_callable=lambda e: [x.value for x in e], create_constraint=False, native_enum=False),
        default=ComplianceStatus.NON_COMPLIANT
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_area: Mapped[str | None] = mapped_column(String(50), nullable=True)
    delta_type: Mapped[str | None] = mapped_column(
        SAEnum(DeltaType, values_callable=lambda e: [x.value for x in e], create_constraint=False, native_enum=False),
        default=DeltaType.UNCHANGED
    )
    routed_agent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fix_status: Mapped[str] = mapped_column(
        SAEnum(FixStatus, values_callable=lambda e: [x.value for x in e], create_constraint=False, native_enum=False),
        default=FixStatus.PENDING
    )
    fixed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fixed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pr_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    scan: Mapped["Scan"] = relationship(back_populates="findings")
    requirement: Mapped["SrcRequirement"] = relationship(back_populates="findings")
    fix_attempts: Mapped[list["FixHistory"]] = relationship(back_populates="finding")

    __table_args__ = (
        Index("ix_findings_component", "component"),
        Index("ix_findings_status", "status"),
        Index("ix_findings_fix_status", "fix_status"),
        Index("ix_findings_category", "category"),
    )


class FixHistory(Base):
    __tablename__ = "fix_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("src_findings.id"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    agent_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_result: Mapped[str | None] = mapped_column(String(20), nullable=True)  # pass/fail
    pr_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    finding: Mapped["SrcFinding"] = relationship(back_populates="fix_attempts")


class ReportUpdate(Base):
    __tablename__ = "report_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), nullable=False)
    regenerated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    trigger: Mapped[str | None] = mapped_column(String(50), nullable=True)  # fix_applied, manual
    changes_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScanReport(Base):
    __tablename__ = "scan_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)  # html, json
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    scan: Mapped["Scan"] = relationship(back_populates="reports")
