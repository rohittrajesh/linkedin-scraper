# src/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import DATABASE_URL, logger

# ─── Base class for our models ─────────────────────────────────────────────────────
Base = declarative_base()

# ─── Engine & Session factory ───────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """
    Create all tables in the database (if they don’t exist).
    """
    logger.info("Initializing database tables...")
    # Import all models so that Base.metadata is populated
    import src.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependency‐style session generator (for FastAPI later).
    Yields a session and closes it automatically.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
