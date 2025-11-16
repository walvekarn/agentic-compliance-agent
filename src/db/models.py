"""Database models"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
from datetime import datetime
from .base import Base


class ComplianceQuery(Base):
    """Model for storing compliance queries and responses"""
    
    __tablename__ = "compliance_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model = Column(String(100), nullable=False)
    status = Column(String(50), default="success")
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ComplianceQuery(id={self.id}, query='{self.query[:50]}...')>"


class ComplianceRule(Base):
    """Model for storing compliance rules"""
    
    __tablename__ = "compliance_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    regulation_source = Column(String(255), nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ComplianceRule(id={self.id}, title='{self.title}')>"


class AuditTrail(Base):
    """Model for storing agent decision audit trail"""
    
    __tablename__ = "audit_trail"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core identification
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    agent_type = Column(String(100), nullable=False, index=True)  # 'decision_engine' or 'openai_agent'
    
    # Task information
    task_description = Column(Text, nullable=False)
    task_category = Column(String(100), nullable=True, index=True)
    
    # Entity information
    entity_name = Column(String(255), nullable=True, index=True)
    entity_type = Column(String(100), nullable=True)
    
    # Decision information
    decision_outcome = Column(String(50), nullable=False, index=True)  # AUTONOMOUS, REVIEW_REQUIRED, ESCALATE
    confidence_score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=True, index=True)  # LOW, MEDIUM, HIGH
    risk_score = Column(Float, nullable=True)
    
    # Reasoning chain (stored as JSON array)
    reasoning_chain = Column(JSON, nullable=False)
    
    # Additional context
    risk_factors = Column(JSON, nullable=True)  # Detailed risk breakdown
    recommendations = Column(JSON, nullable=True)  # Action recommendations
    escalation_reason = Column(Text, nullable=True)
    
    # Full context (for detailed analysis)
    entity_context = Column(JSON, nullable=True)
    task_context = Column(JSON, nullable=True)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<AuditTrail(id={self.id}, timestamp={self.timestamp}, decision={self.decision_outcome})>"
    
    def to_dict(self):
        """Convert audit trail entry to dictionary for JSON output"""
        return {
            "audit_id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "agent_type": self.agent_type,
            "task": {
                "description": self.task_description,
                "category": self.task_category
            },
            "entity": {
                "name": self.entity_name,
                "type": self.entity_type
            },
            "decision": {
                "outcome": self.decision_outcome,
                "confidence_score": self.confidence_score,
                "risk_level": self.risk_level,
                "risk_score": self.risk_score
            },
            "reasoning_chain": self.reasoning_chain,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
            "escalation_reason": self.escalation_reason,
            "entity_context": self.entity_context,
            "task_context": self.task_context,
            "metadata": self.meta_data
        }


class FeedbackLog(Base):
    """Model for storing human feedback on AI decisions"""
    
    __tablename__ = "feedback_log"
    
    feedback_id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Context
    entity_name = Column(String(255), nullable=True, index=True)
    task_description = Column(Text, nullable=False)
    
    # Decisions
    ai_decision = Column(String(50), nullable=False, index=True)  # AUTONOMOUS, REVIEW_REQUIRED, ESCALATE
    human_decision = Column(String(50), nullable=False, index=True)  # AUTONOMOUS, REVIEW_REQUIRED, ESCALATE
    
    # Feedback details
    notes = Column(Text, nullable=True)
    
    # Agreement flag (computed)
    is_agreement = Column(Integer, nullable=False)  # 1 if ai_decision == human_decision, 0 otherwise
    
    # Link to audit trail if available
    audit_trail_id = Column(Integer, nullable=True, index=True)
    
    # Additional metadata
    meta_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<FeedbackLog(id={self.feedback_id}, ai={self.ai_decision}, human={self.human_decision}, agree={bool(self.is_agreement)})>"
    
    def to_dict(self):
        """Convert feedback log entry to dictionary for JSON output"""
        return {
            "feedback_id": self.feedback_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "entity_name": self.entity_name,
            "task_description": self.task_description,
            "ai_decision": self.ai_decision,
            "human_decision": self.human_decision,
            "notes": self.notes,
            "is_agreement": bool(self.is_agreement),
            "audit_trail_id": self.audit_trail_id,
            "metadata": self.meta_data
        }


class EntityHistory(Base):
    """Model for storing organization decision history for contextual learning"""
    
    __tablename__ = "entity_history"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_name = Column(String(255), nullable=False, index=True)
    task_category = Column(String(100), nullable=False, index=True)
    decision = Column(String(50), nullable=False, index=True)  # AUTONOMOUS, REVIEW_REQUIRED, ESCALATE
    risk_level = Column(String(50), nullable=True, index=True)  # LOW, MEDIUM, HIGH
    confidence_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Additional context for richer memory
    task_description = Column(Text, nullable=True)
    jurisdictions = Column(JSON, nullable=True)
    
    # Metadata
    meta_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<EntityHistory(id={self.id}, entity={self.entity_name}, category={self.task_category}, decision={self.decision})>"
    
    def to_dict(self):
        """Convert entity history entry to dictionary for JSON output"""
        return {
            "id": self.id,
            "entity_name": self.entity_name,
            "task_category": self.task_category,
            "decision": self.decision,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "risk_score": self.risk_score,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "task_description": self.task_description,
            "jurisdictions": self.jurisdictions,
            "metadata": self.meta_data
        }

