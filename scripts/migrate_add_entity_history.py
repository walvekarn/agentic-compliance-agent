"""
Database Migration: Add entity_history table

This script creates the entity_history table for storing organization decision history
to enable contextual learning and pattern recognition.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.base import engine, Base
from src.db.models import EntityHistory

def migrate():
    """Create entity_history table"""
    print("=" * 70)
    print("Database Migration: Adding entity_history table")
    print("=" * 70)
    
    try:
        # Create all tables (this will only create missing ones)
        Base.metadata.create_all(bind=engine)
        
        print("\n✅ Migration complete!")
        print("\nThe following table has been created:")
        print("  • entity_history - Stores organization decision history")
        print("\nColumns:")
        print("  • id (Primary Key)")
        print("  • entity_name (indexed)")
        print("  • task_category (indexed)")
        print("  • decision (indexed)")
        print("  • risk_level (indexed)")
        print("  • confidence_score")
        print("  • risk_score")
        print("  • timestamp (indexed)")
        print("  • task_description")
        print("  • jurisdictions (JSON)")
        print("  • meta_data (JSON)")
        print("\n" + "=" * 70)
        print("Agent now has persistent memory!")
        print("Every decision will be remembered for contextual awareness.")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)

