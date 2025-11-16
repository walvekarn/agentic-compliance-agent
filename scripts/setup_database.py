"""
Setup database for development.

Run: python scripts/setup_database.py

This script initializes the database and creates all necessary tables.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.base import engine, Base
from src.db import models  # noqa: F401 - Import to register models


def setup_database():
    """Initialize database with all tables."""
    print("📊 Setting up database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        print(f"📁 Database location: {engine.url}")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    setup_database()

