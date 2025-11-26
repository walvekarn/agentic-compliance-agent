"""
Audit Entry Converter
=====================
Converts database audit entries to unified AuditEntry schema format.
"""

from typing import Dict, Any
from backend.db.models import AuditTrail
from shared.schemas.audit_entry import AuditEntry, DecisionOutcome, RiskLevel
from datetime import datetime


def convert_audit_trail_to_audit_entry(audit_trail: AuditTrail) -> Dict[str, Any]:
    """
    Convert AuditTrail database model to unified AuditEntry schema format.
    
    Args:
        audit_trail: AuditTrail database model
        
    Returns:
        Dictionary matching AuditEntry schema exactly
    """
    # Convert decision outcome
    try:
        decision_outcome = DecisionOutcome(audit_trail.decision_outcome)
    except ValueError:
        # Fallback for legacy values
        decision_outcome = DecisionOutcome.REVIEW_REQUIRED
    
    # Convert risk level
    risk_level = None
    if audit_trail.risk_level:
        try:
            risk_level = RiskLevel(audit_trail.risk_level)
        except ValueError:
            risk_level = None
    
    # Build audit entry dict
    audit_entry_dict = {
        "audit_id": audit_trail.id,
        "timestamp": audit_trail.timestamp,
        "agent_type": audit_trail.agent_type,
        "task_description": audit_trail.task_description,
        "task_category": audit_trail.task_category,
        "entity_name": audit_trail.entity_name,
        "entity_type": audit_trail.entity_type,
        "decision_outcome": decision_outcome.value,
        "confidence_score": audit_trail.confidence_score,
        "risk_level": risk_level.value if risk_level else None,
        "risk_score": audit_trail.risk_score,
        "reasoning_chain": audit_trail.reasoning_chain if isinstance(audit_trail.reasoning_chain, list) else [],
        "risk_factors": audit_trail.risk_factors,
        "recommendations": audit_trail.recommendations,
        "escalation_reason": audit_trail.escalation_reason,
        "entity_context": audit_trail.entity_context,
        "task_context": audit_trail.task_context,
        "metadata": audit_trail.meta_data or {}
    }
    
    # Remove None values for optional fields (except those that should be None)
    cleaned = {}
    for key, value in audit_entry_dict.items():
        if value is not None or key in ["risk_level", "risk_score", "task_category", "entity_name", "entity_type"]:
            cleaned[key] = value
    
    return cleaned

