"""
Dependency Injection Factories

FastAPI dependency factories for services and repositories.
"""

from functools import lru_cache
from sqlalchemy.orm import Session
from fastapi import Depends

from src.db.base import get_db
from src.repositories.entity_history_repository import EntityHistoryRepository
from src.repositories.audit_trail_repository import AuditTrailRepository
from src.repositories.compliance_query_repository import ComplianceQueryRepository
from src.repositories.feedback_repository import FeedbackRepository
from src.services.pattern_service import PatternService
from src.services.audit_service import AuditService
from src.services.decision_service import DecisionService
from src.services.compliance_query_service import ComplianceQueryService
from src.agent.decision_engine import DecisionEngine
from src.agent.openai_agent import ComplianceAgent


# Repository Dependencies
def get_entity_history_repository(db: Session = Depends(get_db)) -> EntityHistoryRepository:
    """Get entity history repository"""
    return EntityHistoryRepository(db)


def get_audit_trail_repository(db: Session = Depends(get_db)) -> AuditTrailRepository:
    """Get audit trail repository"""
    return AuditTrailRepository(db)


def get_compliance_query_repository(db: Session = Depends(get_db)) -> ComplianceQueryRepository:
    """Get compliance query repository"""
    return ComplianceQueryRepository(db)


def get_feedback_repository(db: Session = Depends(get_db)) -> FeedbackRepository:
    """Get feedback repository"""
    return FeedbackRepository(db)


# Service Dependencies
@lru_cache()
def get_decision_engine() -> DecisionEngine:
    """Get decision engine (singleton)"""
    return DecisionEngine()


@lru_cache()
def get_compliance_agent() -> ComplianceAgent:
    """Get compliance agent (singleton)"""
    return ComplianceAgent()


def get_pattern_service(
    entity_repo: EntityHistoryRepository = Depends(get_entity_history_repository)
) -> PatternService:
    """Get pattern service"""
    return PatternService(entity_repo)


def get_audit_service(
    audit_repo: AuditTrailRepository = Depends(get_audit_trail_repository)
) -> AuditService:
    """Get audit service"""
    return AuditService(audit_repo)


def get_decision_service(
    decision_engine: DecisionEngine = Depends(get_decision_engine),
    entity_repo: EntityHistoryRepository = Depends(get_entity_history_repository),
    compliance_query_repo: ComplianceQueryRepository = Depends(get_compliance_query_repository),
    audit_trail_repo: AuditTrailRepository = Depends(get_audit_trail_repository),
    audit_service: AuditService = Depends(get_audit_service),
    pattern_service: PatternService = Depends(get_pattern_service)
) -> DecisionService:
    """Get decision service"""
    return DecisionService(
        decision_engine=decision_engine,
        entity_repository=entity_repo,
        compliance_query_repository=compliance_query_repo,
        audit_trail_repository=audit_trail_repo,
        audit_service=audit_service,
        pattern_service=pattern_service
    )


def get_compliance_query_service(
    agent: ComplianceAgent = Depends(get_compliance_agent),
    compliance_query_repo: ComplianceQueryRepository = Depends(get_compliance_query_repository)
) -> ComplianceQueryService:
    """Get compliance query service"""
    return ComplianceQueryService(agent, compliance_query_repo)

