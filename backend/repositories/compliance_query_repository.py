"""
Compliance Query Repository

Handles data access for compliance queries.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from backend.db.models import ComplianceQuery
from .base_repository import BaseRepository


class ComplianceQueryRepository(BaseRepository[ComplianceQuery]):
    """Repository for ComplianceQuery model"""
    
    def create(self, entity: ComplianceQuery) -> ComplianceQuery:
        """Create a new compliance query"""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[ComplianceQuery]:
        """Get compliance query by ID"""
        return self.db.query(ComplianceQuery).filter(ComplianceQuery.id == entity_id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[ComplianceQuery]:
        """Get all compliance queries"""
        query = self.db.query(ComplianceQuery)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.order_by(ComplianceQuery.created_at.desc()).all()
    
    def update(self, entity: ComplianceQuery) -> ComplianceQuery:
        """Update compliance query"""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete compliance query"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

