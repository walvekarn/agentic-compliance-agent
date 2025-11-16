"""
Entity History Repository

Handles data access for entity decision history.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.models import EntityHistory
from .base_repository import BaseRepository


class EntityHistoryRepository(BaseRepository[EntityHistory]):
    """Repository for EntityHistory model"""
    
    def create(self, entity: EntityHistory) -> EntityHistory:
        """Create a new entity history entry"""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[EntityHistory]:
        """Get entity history by ID"""
        return self.db.query(EntityHistory).filter(EntityHistory.id == entity_id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[EntityHistory]:
        """Get all entity history entries"""
        query = self.db.query(EntityHistory)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update(self, entity: EntityHistory) -> EntityHistory:
        """Update entity history entry"""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete entity history entry"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False
    
    def find_by_entity_and_category(
        self,
        entity_name: str,
        task_category: str,
        limit: int = 5
    ) -> List[EntityHistory]:
        """
        Find similar cases for entity and task category.
        
        Args:
            entity_name: Entity name
            task_category: Task category
            limit: Maximum number of results
            
        Returns:
            List of matching entity history entries
        """
        return self.db.query(EntityHistory).filter(
            and_(
                EntityHistory.entity_name == entity_name,
                EntityHistory.task_category == task_category
            )
        ).order_by(EntityHistory.timestamp.desc()).limit(limit).all()

