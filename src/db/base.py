"""Database configuration and base models"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.config.config_provider import get_settings


def create_database_engine():
    """
    Factory function for database engine using settings.
    
    Returns:
        SQLAlchemy engine with proper connection pooling
    """
    settings = get_settings()
    
    # Build connection args
    connect_args = {}
    if "sqlite" in settings.database_url:
        connect_args["check_same_thread"] = False
    
    # Create engine with connection pooling
    engine = create_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,  # Verify connections before using
        connect_args=connect_args,
    )
    return engine


# Create engine using settings
engine = create_database_engine()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


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

