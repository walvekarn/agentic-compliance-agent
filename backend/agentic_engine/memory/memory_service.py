"""
Simple Memory Service

A simple demo implementation that saves and retrieves memory records.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone

from backend.db.models import MemoryRecord


class MemoryService:
    """Simple memory service for storing and retrieving agent memories"""
    
    def __init__(self, db_session: Session):
        """
        Initialize memory service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def save_memory(
        self,
        memory_key: str,
        content: Dict[str, Any],
        memory_type: str = "episodic",
        entity_name: Optional[str] = None,
        task_category: Optional[str] = None,
        summary: Optional[str] = None,
        importance_score: float = 0.5
    ) -> MemoryRecord:
        """
        Save a memory record.
        
        Args:
            memory_key: Unique key for this memory
            content: Memory content (dict)
            memory_type: Type of memory (episodic, semantic, working)
            entity_name: Optional entity name
            task_category: Optional task category
            summary: Optional human-readable summary
            importance_score: Importance score (0.0 to 1.0)
        
        Returns:
            Created MemoryRecord
        """
        try:
            # Check if memory already exists
            existing = self.db.query(MemoryRecord).filter(
                MemoryRecord.memory_key == memory_key
            ).first()
            
            if existing:
                # Update existing memory
                existing.content = content
                existing.summary = summary or existing.summary
                existing.importance_score = importance_score
                existing.entity_name = entity_name or existing.entity_name
                existing.task_category = task_category or existing.task_category
                existing.updated_at = datetime.now(timezone.utc)
                existing.access_count += 1
                existing.last_accessed = datetime.now(timezone.utc)
                self.db.commit()
                return existing
            else:
                # Create new memory
                memory = MemoryRecord(
                    memory_key=memory_key,
                    memory_type=memory_type,
                    content=content,
                    summary=summary,
                    entity_name=entity_name,
                    task_category=task_category,
                    importance_score=importance_score,
                    access_count=1,
                    last_accessed=datetime.now(timezone.utc)
                )
                self.db.add(memory)
                self.db.commit()
                return memory
        
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to save memory: {str(e)}")
    
    def get_memory(self, memory_key: str) -> Optional[MemoryRecord]:
        """
        Retrieve a memory by key.
        
        Args:
            memory_key: Memory key to retrieve
        
        Returns:
            MemoryRecord if found, None otherwise
        """
        try:
            memory = self.db.query(MemoryRecord).filter(
                MemoryRecord.memory_key == memory_key
            ).first()
            
            if memory:
                # Update access tracking
                memory.access_count += 1
                memory.last_accessed = datetime.now(timezone.utc)
                self.db.commit()
            
            return memory
        
        except Exception as e:
            return None
    
    def get_memories_for_entity(
        self,
        entity_name: str,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """
        Get memories for a specific entity.
        
        Args:
            entity_name: Entity name
            limit: Maximum number of memories to return
        
        Returns:
            List of MemoryRecord objects
        """
        try:
            memories = self.db.query(MemoryRecord).filter(
                MemoryRecord.entity_name == entity_name
            ).order_by(
                MemoryRecord.importance_score.desc(),
                MemoryRecord.last_accessed.desc()
            ).limit(limit).all()
            
            # Update access tracking
            for memory in memories:
                memory.access_count += 1
                memory.last_accessed = datetime.now(timezone.utc)
            self.db.commit()
            
            return memories
        
        except Exception as e:
            return []
    
    def get_memories_by_type(
        self,
        memory_type: str,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """
        Get memories by type.
        
        Args:
            memory_type: Type of memory (episodic, semantic, working)
            limit: Maximum number of memories to return
        
        Returns:
            List of MemoryRecord objects
        """
        try:
            memories = self.db.query(MemoryRecord).filter(
                MemoryRecord.memory_type == memory_type
            ).order_by(
                MemoryRecord.importance_score.desc(),
                MemoryRecord.last_accessed.desc()
            ).limit(limit).all()
            
            # Update access tracking
            for memory in memories:
                memory.access_count += 1
                memory.last_accessed = datetime.now(timezone.utc)
            self.db.commit()
            
            return memories
        
        except Exception as e:
            return []
    
    def get_recent_memories(self, limit: int = 10) -> List[MemoryRecord]:
        """
        Get most recently accessed memories.
        
        Args:
            limit: Maximum number of memories to return
        
        Returns:
            List of MemoryRecord objects
        """
        try:
            memories = self.db.query(MemoryRecord).order_by(
                MemoryRecord.last_accessed.desc()
            ).limit(limit).all()
            
            return memories
        
        except Exception as e:
            return []
    
    def delete_memory(self, memory_key: str) -> bool:
        """
        Delete a memory record.
        
        Args:
            memory_key: Memory key to delete
        
        Returns:
            True if deleted, False if not found
        """
        try:
            memory = self.db.query(MemoryRecord).filter(
                MemoryRecord.memory_key == memory_key
            ).first()
            
            if memory:
                self.db.delete(memory)
                self.db.commit()
                return True
            
            return False
        
        except Exception as e:
            self.db.rollback()
            return False
