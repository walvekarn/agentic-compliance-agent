"""
Audit Service (Refactored)

Business logic for audit trail operations using repositories.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from src.agent.risk_models import DecisionAnalysis
from src.repositories.audit_trail_repository import AuditTrailRepository
from src.db.models import AuditTrail


class AuditService:
    """Service for audit trail operations"""
    
    def __init__(self, audit_repository: AuditTrailRepository):
        """
        Initialize audit service.
        
        Args:
            audit_repository: Repository for audit trail
        """
        self.audit_repository = audit_repository
    
    def log_decision_analysis(
        self,
        analysis: DecisionAnalysis,
        agent_type: str = "decision_engine",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """
        Log a decision analysis to the audit trail.
        
        Args:
            analysis: DecisionAnalysis object
            agent_type: Type of agent making the decision
            metadata: Additional metadata
            
        Returns:
            Created AuditTrail entry
        """
        # Extract risk factors as dict
        risk_factors_dict = {
            "jurisdiction_risk": analysis.risk_factors.jurisdiction_risk,
            "entity_risk": analysis.risk_factors.entity_risk,
            "task_risk": analysis.risk_factors.task_risk,
            "data_sensitivity_risk": analysis.risk_factors.data_sensitivity_risk,
            "regulatory_risk": analysis.risk_factors.regulatory_risk,
            "impact_risk": analysis.risk_factors.impact_risk,
            "overall_score": analysis.risk_factors.overall_score
        }
        
        # Create audit trail entry
        audit_entry = AuditTrail(
            timestamp=analysis.timestamp,
            agent_type=agent_type,
            task_description=analysis.task_context.description,
            task_category=analysis.task_context.category.value,
            entity_name=analysis.entity_context.name,
            entity_type=analysis.entity_context.entity_type.value,
            decision_outcome=analysis.decision.value,
            confidence_score=analysis.confidence,
            risk_level=analysis.risk_level.value,
            risk_score=analysis.risk_factors.overall_score,
            reasoning_chain=analysis.reasoning,
            risk_factors=risk_factors_dict,
            recommendations=analysis.recommendations,
            escalation_reason=analysis.escalation_reason,
            entity_context=analysis.entity_context.model_dump(mode='json'),
            task_context=analysis.task_context.model_dump(mode='json'),
            meta_data=metadata or {}
        )
        
        return self.audit_repository.create(audit_entry)
    
    def get_audit_trail(
        self,
        limit: int = 100,
        offset: int = 0,
        agent_type: Optional[str] = None,
        entity_name: Optional[str] = None,
        decision_outcome: Optional[str] = None,
        risk_level: Optional[str] = None,
        task_category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditTrail]:
        """
        Retrieve audit trail entries with optional filters.
        
        Args:
            limit: Maximum number of entries
            offset: Number of entries to skip
            agent_type: Filter by agent type
            entity_name: Filter by entity name
            decision_outcome: Filter by decision outcome
            risk_level: Filter by risk level
            task_category: Filter by task category
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of AuditTrail entries
        """
        filters = {}
        if agent_type:
            filters["agent_type"] = agent_type
        if entity_name:
            filters["entity_name"] = entity_name
        if decision_outcome:
            filters["decision_outcome"] = decision_outcome
        if risk_level:
            filters["risk_level"] = risk_level
        if task_category:
            filters["task_category"] = task_category
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        
        return self.audit_repository.get_all(limit=limit, offset=offset, filters=filters)
    
    def get_audit_entry(self, audit_id: int) -> Optional[AuditTrail]:
        """Get audit entry by ID"""
        return self.audit_repository.get_by_id(audit_id)

