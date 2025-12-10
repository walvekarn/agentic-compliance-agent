"""
Simple Memory Demo

Demonstrates the memory system working:
1. Save memories for different entities/tasks
2. Retrieve memories by entity
3. Show memory access tracking
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from backend.db.base import SessionLocal, engine, Base
from backend.db.models import MemoryRecord
from backend.agentic_engine.memory import MemoryService


def create_tables():
    """Create database tables if they don't exist"""
    Base.metadata.create_all(bind=engine)


def demo_memory():
    """Run memory demo"""
    print("=" * 60)
    print("🧠 Memory System Demo")
    print("=" * 60)
    print()
    
    # Create tables
    create_tables()
    
    # Get database session
    db: Session = SessionLocal()
    
    try:
        # Initialize memory service
        memory_service = MemoryService(db)
        
        print("1️⃣  Saving Memories")
        print("-" * 60)
        
        # Save some memories
        memory1 = memory_service.save_memory(
            memory_key="demo_entity1_task1",
            content={
                "entity": "DemoCorp",
                "task": "GDPR compliance review",
                "decision": "REVIEW_REQUIRED",
                "risk_level": "MEDIUM",
                "notes": "First time handling GDPR for this entity"
            },
            memory_type="episodic",
            entity_name="DemoCorp",
            task_category="DATA_PRIVACY",
            summary="DemoCorp GDPR compliance review - REVIEW_REQUIRED",
            importance_score=0.8
        )
        print(f"✅ Saved memory: {memory1.memory_key}")
        print(f"   Summary: {memory1.summary}")
        print()
        
        memory2 = memory_service.save_memory(
            memory_key="demo_entity1_task2",
            content={
                "entity": "DemoCorp",
                "task": "HIPAA breach notification",
                "decision": "ESCALATE",
                "risk_level": "HIGH",
                "notes": "Data breach requires immediate escalation"
            },
            memory_type="episodic",
            entity_name="DemoCorp",
            task_category="DATA_PRIVACY",
            summary="DemoCorp HIPAA breach - ESCALATE",
            importance_score=0.9
        )
        print(f"✅ Saved memory: {memory2.memory_key}")
        print(f"   Summary: {memory2.summary}")
        print()
        
        memory3 = memory_service.save_memory(
            memory_key="demo_entity2_task1",
            content={
                "entity": "StartupTech",
                "task": "Internal policy update",
                "decision": "AUTONOMOUS",
                "risk_level": "LOW",
                "notes": "Simple internal policy, low risk"
            },
            memory_type="episodic",
            entity_name="StartupTech",
            task_category="GENERAL_INQUIRY",
            summary="StartupTech policy update - AUTONOMOUS",
            importance_score=0.5
        )
        print(f"✅ Saved memory: {memory3.memory_key}")
        print(f"   Summary: {memory3.summary}")
        print()
        
        print("2️⃣  Retrieving Memory by Key")
        print("-" * 60)
        
        retrieved = memory_service.get_memory("demo_entity1_task1")
        if retrieved:
            print(f"✅ Retrieved: {retrieved.memory_key}")
            print(f"   Content: {retrieved.content}")
            print(f"   Access count: {retrieved.access_count}")
            print(f"   Last accessed: {retrieved.last_accessed}")
            print()
        
        print("3️⃣  Retrieving Memories by Entity")
        print("-" * 60)
        
        demo_corp_memories = memory_service.get_memories_for_entity("DemoCorp", limit=10)
        print(f"✅ Found {len(demo_corp_memories)} memories for DemoCorp:")
        for mem in demo_corp_memories:
            print(f"   - {mem.memory_key}: {mem.summary}")
            print(f"     Importance: {mem.importance_score}, Accesses: {mem.access_count}")
        print()
        
        print("4️⃣  Retrieving Recent Memories")
        print("-" * 60)
        
        recent = memory_service.get_recent_memories(limit=5)
        print(f"✅ Found {len(recent)} recent memories:")
        for mem in recent:
            print(f"   - {mem.memory_key} ({mem.entity_name})")
            print(f"     Last accessed: {mem.last_accessed}")
        print()
        
        print("5️⃣  Memory Access Tracking")
        print("-" * 60)
        
        # Access the same memory multiple times
        for i in range(3):
            mem = memory_service.get_memory("demo_entity1_task1")
            if mem:
                print(f"   Access #{i+1}: access_count = {mem.access_count}")
        print()
        
        print("6️⃣  Updating Memory")
        print("-" * 60)
        
        updated = memory_service.save_memory(
            memory_key="demo_entity1_task1",
            content={
                "entity": "DemoCorp",
                "task": "GDPR compliance review",
                "decision": "REVIEW_REQUIRED",
                "risk_level": "MEDIUM",
                "notes": "Updated: Follow-up review completed",
                "updated": True
            },
            summary="DemoCorp GDPR compliance review - UPDATED",
            importance_score=0.85
        )
        print(f"✅ Updated memory: {updated.memory_key}")
        print(f"   New summary: {updated.summary}")
        print(f"   Updated at: {updated.updated_at}")
        print()
        
        print("=" * 60)
        print("✅ Demo Complete!")
        print("=" * 60)
        print()
        print("Memory system is working! Memories are:")
        print("  - Saved to database (memory_records table)")
        print("  - Retrievable by key, entity, or type")
        print("  - Track access counts and last accessed time")
        print("  - Updateable when new information arrives")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    demo_memory()
