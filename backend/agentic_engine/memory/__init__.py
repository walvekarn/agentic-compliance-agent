"""
Memory Module
==============

This module provides memory management capabilities for the agentic AI engine,
enabling persistent learning and context retention across sessions.

**Status:** PHASE 3 - Partially Implemented

**Core Components:**

1. **MemoryStore** - Central memory storage interface
   - Provides unified interface for memory operations
   - Supports key-value storage and retrieval
   - Enables semantic search across memories
   - Currently a stub implementation (PHASE 3)

2. **EpisodicMemory** - Event-based memory system
   - Stores specific events and experiences
   - Tracks temporal sequences of actions
   - Enables "remembering" past decisions and outcomes
   - Status: PHASE 3 - Not yet fully implemented

3. **SemanticMemory** - Knowledge-based memory system
   - Stores abstract knowledge and patterns
   - Enables generalization across similar cases
   - Supports concept-based retrieval
   - Status: PHASE 3 - Not yet fully implemented

**Planned Features (PHASE 3):**

- Database persistence for memories
- Memory retrieval by similarity
- Memory consolidation and forgetting
- Cross-entity memory patterns
- Integration with ScoreAssistant

**Usage (Future):**

```python
# Store episodic memory
from backend.agentic_engine.memory import EpisodicMemory

memory = EpisodicMemory(db_session=db)
memory.store_event(
    entity_name="Company A",
    event_type="decision",
    context={"task": "GDPR compliance", "decision": "AUTONOMOUS"},
    timestamp=datetime.now()
)

# Retrieve similar memories
similar = memory.retrieve_similar(
    query="GDPR compliance for tech company",
    limit=5
)

# Semantic memory
from backend.agentic_engine.memory import SemanticMemory

semantic = SemanticMemory(db_session=db)
semantic.store_pattern(
    pattern="Tech companies in EU often need GDPR Article 30 records",
    confidence=0.85
)
```

**Note:** This module is marked for PHASE 3 implementation. Current system
uses in-memory storage only. Full persistence and advanced features coming
in future releases.
"""

from .memory_store import MemoryStore
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory

__all__ = [
    "MemoryStore",
    "EpisodicMemory",
    "SemanticMemory",
]

