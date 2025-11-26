"""
Unified Audit Entry Schema
===========================
Standardized audit entry format for all compliance requests.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .analysis_result import DecisionOutcome, RiskLevel


class AuditEntry(BaseModel):
    """Unified audit entry schema"""
    audit_id: Optional[int] = Field(default=None, description="Audit entry ID")
    timestamp: datetime = Field(description="Timestamp of the decision")
    agent_type: str = Field(description="Type of agent making the decision")
    
    # Task information
    task_description: str = Field(description="Description of the task")
    task_category: Optional[str] = Field(default=None, description="Task category")
    
    # Entity information
    entity_name: Optional[str] = Field(default=None, description="Entity name")
    entity_type: Optional[str] = Field(default=None, description="Entity type")
    
    # Decision information
    decision_outcome: DecisionOutcome = Field(description="Decision outcome")
    confidence_score: float = Field(ge=0, le=1, description="Confidence score (0-1)")
    risk_level: Optional[RiskLevel] = Field(default=None, description="Risk level")
    risk_score: Optional[float] = Field(default=None, ge=0, le=1, description="Risk score (0-1)")
    
    # Reasoning and context
    reasoning_chain: List[str] = Field(description="Reasoning chain")
    risk_factors: Optional[Dict[str, Any]] = Field(default=None, description="Risk factors breakdown")
    recommendations: Optional[List[str]] = Field(default=None, description="Recommendations")
    escalation_reason: Optional[str] = Field(default=None, description="Escalation reason")
    
    # Full context
    entity_context: Optional[Dict[str, Any]] = Field(default=None, description="Full entity context")
    task_context: Optional[Dict[str, Any]] = Field(default=None, description="Full task context")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": 1,
                "timestamp": "2025-01-15T10:30:00Z",
                "agent_type": "decision_engine",
                "task_description": "GDPR compliance review",
                "task_category": "DATA_PRIVACY",
                "entity_name": "TechCorp",
                "entity_type": "PRIVATE_COMPANY",
                "decision_outcome": "REVIEW_REQUIRED",
                "confidence_score": 0.85,
                "risk_level": "MEDIUM",
                "risk_score": 0.65,
                "reasoning_chain": [
                    "Entity operates in EU jurisdiction",
                    "Task involves personal data processing"
                ],
                "risk_factors": {
                    "jurisdiction_risk": 0.7,
                    "entity_risk": 0.5
                }
            }
        }

