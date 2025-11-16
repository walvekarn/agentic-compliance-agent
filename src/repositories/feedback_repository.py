"""
Feedback Repository

Handles data access for feedback logs.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.db.models import FeedbackLog
from .base_repository import BaseRepository


class FeedbackRepository(BaseRepository[FeedbackLog]):
    """Repository for FeedbackLog model"""
    
    def create(self, entity: FeedbackLog) -> FeedbackLog:
        """Create a new feedback log entry"""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[FeedbackLog]:
        """Get feedback log by ID"""
        return self.db.query(FeedbackLog).filter(FeedbackLog.feedback_id == entity_id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[FeedbackLog]:
        """Get all feedback log entries"""
        query = self.db.query(FeedbackLog)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.order_by(FeedbackLog.timestamp.desc()).all()
    
    def update(self, entity: FeedbackLog) -> FeedbackLog:
        """Update feedback log entry"""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete feedback log entry"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

