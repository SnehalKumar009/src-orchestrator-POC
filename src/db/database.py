from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """Create all tables."""
    from src.db.models import (
        Scan, SrcFinding, SrcRequirement, FixHistory, ReportUpdate, ScanReport
    )
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a new DB session."""
    return SessionLocal()
