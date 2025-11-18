"""
Audit Trail Repository

Handles data access for audit trail entries.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models import AuditTrail
from .base_repository import BaseRepository


class AuditTrailRepository(BaseRepository[AuditTrail]):
    """Repository for AuditTrail model"""
    
    def create(self, entity: AuditTrail) -> AuditTrail:
        """Create a new audit trail entry"""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[AuditTrail]:
        """Get audit trail entry by ID"""
        return self.db.query(AuditTrail).filter(AuditTrail.id == entity_id).first()
    
    def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AuditTrail]:
        """
        Get all audit trail entries with optional filters.
        
        Args:
            limit: Maximum number of entries
            offset: Number of entries to skip
            filters: Optional filter dictionary with keys:
                - agent_type
                - entity_name
                - decision_outcome
                - risk_level
                - task_category
                - start_date
                - end_date
                
        Returns:
            List of audit trail entries
        """
        query = self.db.query(AuditTrail)
        
        if filters:
            if filters.get("agent_type"):
                query = query.filter(AuditTrail.agent_type == filters["agent_type"])
            if filters.get("entity_name"):
                query = query.filter(AuditTrail.entity_name == filters["entity_name"])
            if filters.get("decision_outcome"):
                query = query.filter(AuditTrail.decision_outcome == filters["decision_outcome"])
            if filters.get("risk_level"):
                query = query.filter(AuditTrail.risk_level == filters["risk_level"])
            if filters.get("task_category"):
                query = query.filter(AuditTrail.task_category == filters["task_category"])
            if filters.get("start_date"):
                query = query.filter(AuditTrail.timestamp >= filters["start_date"])
            if filters.get("end_date"):
                query = query.filter(AuditTrail.timestamp <= filters["end_date"])
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.order_by(AuditTrail.timestamp.desc()).all()
    
    def update(self, entity: AuditTrail) -> AuditTrail:
        """Update audit trail entry"""
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete audit trail entry"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

