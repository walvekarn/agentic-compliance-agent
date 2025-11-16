"""
Database Migration: Add feedback_log table

This script creates the feedback_log table for storing human feedback on AI decisions.
Run this after updating the models to ensure the database schema is current.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.base import engine, Base
from src.db.models import FeedbackLog

def migrate():
    """Create feedback_log table"""
    print("=" * 70)
    print("Database Migration: Adding feedback_log table")
    print("=" * 70)
    
    try:
        # Create all tables (this will only create missing ones)
        Base.metadata.create_all(bind=engine)
        
        print("\n✅ Migration complete!")
        print("\nThe following table has been created:")
        print("  • feedback_log - Stores human feedback on AI decisions")
        print("\nColumns:")
        print("  • feedback_id (Primary Key)")
        print("  • timestamp")
        print("  • entity_name")
        print("  • task_description")
        print("  • ai_decision")
        print("  • human_decision")
        print("  • notes")
        print("  • is_agreement (computed)")
        print("  • audit_trail_id (optional link)")
        print("  • meta_data (JSON)")
        print("\n" + "=" * 70)
        print("You can now use the feedback system!")
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

