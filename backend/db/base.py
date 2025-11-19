"""Database configuration and base models"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


def create_database_engine():
    """
    Factory function for database engine using settings.
    
    Returns:
        SQLAlchemy engine with proper connection pooling
    """
    # Build connection args
    connect_args = {}
    if "sqlite" in settings.DATABASE_URL:
        connect_args["check_same_thread"] = False
    
    # Create engine with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        connect_args=connect_args,
    )
    return engine


# Create engine using settings
engine = create_database_engine()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SQLAlchemy 2.0 Declarative Base
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


def get_database_type() -> str:
    """
    Detect database type from DATABASE_URL
    
    Returns:
        Database type string: "sqlite", "postgresql", "mysql", etc.
    """
    url = settings.DATABASE_URL.lower()
    if "sqlite" in url:
        return "sqlite"
    elif "postgresql" in url or "postgres" in url:
        return "postgresql"
    elif "mysql" in url:
        return "mysql"
    else:
        # Default to sqlite for unknown types
        return "sqlite"


def get_db():
    """
    Dependency function to get database session
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

