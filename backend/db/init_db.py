"""
Database Initialization Script
==============================
Initialize database tables using SQLAlchemy models.

Usage:
    python -m src.db.init_db
    or
    from backend.db.init_db import init_database
    init_database()
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.db.base import Base, engine
from backend.config import settings

# Import all models to ensure they're registered with Base.metadata
import backend.db.models  # noqa: F401
import backend.auth.auth_models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_database(drop_existing: bool = False):
    """
    Initialize database tables.
    
    Args:
        drop_existing: If True, drop all existing tables before creating new ones.
                      WARNING: This will delete all data!
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Initializing database: {settings.DATABASE_URL}")
        
        if drop_existing:
            logger.warning("Dropping all existing tables...")
            Base.metadata.drop_all(bind=engine)
            logger.info("All tables dropped")
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # List created tables
        tables = list(Base.metadata.tables.keys())
        logger.info(f"Successfully created {len(tables)} table(s):")
        for table in sorted(tables):
            logger.info(f"  - {table}")
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        return False


def verify_tables():
    """
    Verify that all expected tables exist.
    
    Returns:
        Dictionary with table existence status
    """
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    expected_tables = {
        "compliance_queries",
        "compliance_rules",
        "audit_trail",
        "feedback_log",
        "entity_history",
        "memory_records",
        "users",  # From auth.models
    }
    
    status = {}
    for table in expected_tables:
        status[table] = table in existing_tables
    
    return status


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize database tables")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all existing tables before creating new ones (WARNING: deletes all data!)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify table existence after initialization"
    )
    
    args = parser.parse_args()
    
    success = init_database(drop_existing=args.drop)
    
    if success and args.verify:
        logger.info("\nVerifying tables...")
        status = verify_tables()
        for table, exists in sorted(status.items()):
            status_icon = "✅" if exists else "❌"
            logger.info(f"{status_icon} {table}: {'exists' if exists else 'missing'}")
    
    sys.exit(0 if success else 1)

