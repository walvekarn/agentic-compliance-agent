# Memory System Demo

This demo shows the memory system working in the agentic compliance agent.

## What It Demonstrates

1. **Saving Memories**: Store episodic memories of tasks and decisions
2. **Retrieving Memories**: Get memories by key, entity, or type
3. **Access Tracking**: Automatically track how often memories are accessed
4. **Memory Updates**: Update existing memories with new information

## Running the Demo

```bash
# From the project root
cd backend
python demos/memory_demo.py
```

## What You'll See

The demo will:
- Save 3 sample memories for different entities/tasks
- Retrieve a memory by its key
- Get all memories for a specific entity (DemoCorp)
- Show recent memories
- Demonstrate access count tracking
- Update an existing memory

## Memory Integration

The memory system is integrated into `AgentLoop`:

- When `enable_memory=True` and a `db_session` is provided, the agent loop automatically saves execution memories
- Memories include: entity, task, success status, risk assessment, and recommendations
- Memory keys are generated from entity name and task hash

## Example Usage in Agent Loop

```python
from backend.db.base import get_db
from backend.agentic_engine.agent_loop import AgentLoop

db = next(get_db())
agent = AgentLoop(
    enable_memory=True,
    db_session=db
)

result = agent.execute(
    entity="MyCompany",
    task="GDPR compliance review"
)

# Memory is automatically saved if enable_memory=True
if result.get("memory_saved"):
    print("Memory saved successfully!")
```

## Memory Service API

```python
from backend.agentic_engine.memory import MemoryService

memory_service = MemoryService(db_session)

# Save memory
memory = memory_service.save_memory(
    memory_key="unique_key",
    content={"task": "example", "decision": "AUTONOMOUS"},
    entity_name="EntityName",
    summary="Human-readable summary"
)

# Get memory
memory = memory_service.get_memory("unique_key")

# Get memories for entity
memories = memory_service.get_memories_for_entity("EntityName")

# Get recent memories
recent = memory_service.get_recent_memories(limit=10)
```
