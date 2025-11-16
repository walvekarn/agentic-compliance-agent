"""Audit trail service for logging agent decisions"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.models import AuditTrail
from src.agent.risk_models import (
    DecisionAnalysis,
    EntityContext,
    TaskContext
)


class AuditService:
    """Service for logging and retrieving agent decisions in audit trail"""
    
    @staticmethod
    def log_decision_analysis(
        db: Session,
        analysis: DecisionAnalysis,
        agent_type: str = "decision_engine",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """
        Log a decision analysis to the audit trail
        
        Args:
            db: Database session
            analysis: DecisionAnalysis object containing full decision details
            agent_type: Type of agent making the decision (decision_engine, openai_agent)
            metadata: Additional metadata to store
            
        Returns:
            AuditTrail object that was created
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
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        return audit_entry
    
    @staticmethod
    def log_custom_decision(
        db: Session,
        task_description: str,
        decision_outcome: str,
        confidence_score: float,
        reasoning_chain: List[str],
        agent_type: str = "openai_agent",
        task_category: Optional[str] = None,
        entity_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        risk_score: Optional[float] = None,
        risk_factors: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        escalation_reason: Optional[str] = None,
        entity_context: Optional[Dict[str, Any]] = None,
        task_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """
        Log a custom decision to the audit trail (for non-DecisionAnalysis scenarios)
        
        Args:
            db: Database session
            task_description: Description of the task
            decision_outcome: Decision made (e.g., AUTONOMOUS, REVIEW_REQUIRED, ESCALATE)
            confidence_score: Confidence in the decision (0-1)
            reasoning_chain: List of reasoning steps
            agent_type: Type of agent making the decision
            task_category: Category of the task
            entity_name: Name of the entity
            entity_type: Type of entity
            risk_level: Risk level (LOW, MEDIUM, HIGH)
            risk_score: Numeric risk score (0-1)
            risk_factors: Dictionary of risk factors
            recommendations: List of recommendations
            escalation_reason: Reason for escalation if applicable
            entity_context: Full entity context
            task_context: Full task context
            metadata: Additional metadata
            
        Returns:
            AuditTrail object that was created
        """
        audit_entry = AuditTrail(
            timestamp=datetime.utcnow(),
            agent_type=agent_type,
            task_description=task_description,
            task_category=task_category,
            entity_name=entity_name,
            entity_type=entity_type,
            decision_outcome=decision_outcome,
            confidence_score=confidence_score,
            risk_level=risk_level,
            risk_score=risk_score,
            reasoning_chain=reasoning_chain,
            risk_factors=risk_factors,
            recommendations=recommendations,
            escalation_reason=escalation_reason,
            entity_context=entity_context,
            task_context=task_context,
            metadata=metadata or {}
        )
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        return audit_entry
    
    @staticmethod
    def get_audit_trail(
        db: Session,
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
        Retrieve audit trail entries with optional filters
        
        Args:
            db: Database session
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            agent_type: Filter by agent type
            entity_name: Filter by entity name
            decision_outcome: Filter by decision outcome
            risk_level: Filter by risk level
            task_category: Filter by task category
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of AuditTrail objects
        """
        query = db.query(AuditTrail)
        
        # Apply filters
        if agent_type:
            query = query.filter(AuditTrail.agent_type == agent_type)
        if entity_name:
            query = query.filter(AuditTrail.entity_name == entity_name)
        if decision_outcome:
            query = query.filter(AuditTrail.decision_outcome == decision_outcome)
        if risk_level:
            query = query.filter(AuditTrail.risk_level == risk_level)
        if task_category:
            query = query.filter(AuditTrail.task_category == task_category)
        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(AuditTrail.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    @staticmethod
    def get_audit_entry(db: Session, audit_id: int) -> Optional[AuditTrail]:
        """
        Retrieve a specific audit trail entry by ID
        
        Args:
            db: Database session
            audit_id: ID of the audit entry
            
        Returns:
            AuditTrail object or None if not found
        """
        return db.query(AuditTrail).filter(AuditTrail.id == audit_id).first()
    
    @staticmethod
    def get_audit_statistics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about audit trail entries
        
        Args:
            db: Database session
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            Dictionary containing statistics
        """
        query = db.query(AuditTrail)
        
        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)
        
        all_entries = query.all()
        total_count = len(all_entries)
        
        if total_count == 0:
            return {
                "total_decisions": 0,
                "by_outcome": {},
                "by_risk_level": {},
                "by_agent_type": {},
                "by_task_category": {},
                "average_confidence": 0,
                "average_risk_score": 0
            }
        
        # Count by decision outcome
        by_outcome = {}
        by_risk_level = {}
        by_agent_type = {}
        by_task_category = {}
        total_confidence = 0
        total_risk_score = 0
        risk_score_count = 0
        
        for entry in all_entries:
            # Count outcomes
            by_outcome[entry.decision_outcome] = by_outcome.get(entry.decision_outcome, 0) + 1
            
            # Count risk levels
            if entry.risk_level:
                by_risk_level[entry.risk_level] = by_risk_level.get(entry.risk_level, 0) + 1
            
            # Count agent types
            by_agent_type[entry.agent_type] = by_agent_type.get(entry.agent_type, 0) + 1
            
            # Count task categories
            if entry.task_category:
                by_task_category[entry.task_category] = by_task_category.get(entry.task_category, 0) + 1
            
            # Sum confidence and risk scores
            total_confidence += entry.confidence_score
            if entry.risk_score is not None:
                total_risk_score += entry.risk_score
                risk_score_count += 1
        
        from datetime import datetime
        return {
            "total_decisions": total_count,
            "high_risk_count": by_risk_level.get("HIGH", 0),
            "medium_risk_count": by_risk_level.get("MEDIUM", 0),
            "low_risk_count": by_risk_level.get("LOW", 0),
            "autonomous_count": by_outcome.get("AUTONOMOUS", 0),
            "review_required_count": by_outcome.get("REVIEW_REQUIRED", 0),
            "escalate_count": by_outcome.get("ESCALATE", 0),
            "by_outcome": by_outcome,
            "by_risk_level": by_risk_level,
            "by_agent_type": by_agent_type,
            "by_task_category": by_task_category,
            "average_confidence": total_confidence / total_count if total_count > 0 else 0,
            "average_risk_score": total_risk_score / risk_score_count if risk_score_count > 0 else 0,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def export_audit_trail_json(
        db: Session,
        limit: Optional[int] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Export audit trail entries as JSON-serializable dictionaries
        
        Args:
            db: Database session
            limit: Maximum number of entries to export
            **filters: Additional filters to apply
            
        Returns:
            List of dictionaries representing audit trail entries
        """
        entries = AuditService.get_audit_trail(
            db,
            limit=limit or 1000,
            **filters
        )
        
        return [entry.to_dict() for entry in entries]

