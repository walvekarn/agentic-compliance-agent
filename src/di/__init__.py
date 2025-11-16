"""
Dependency Injection Layer

Provides dependency factories for FastAPI routes.
"""

from .dependencies import (
    get_entity_history_repository,
    get_audit_trail_repository,
    get_compliance_query_repository,
    get_feedback_repository,
    get_pattern_service,
    get_decision_service,
    get_compliance_query_service,
    get_audit_service,
)

__all__ = [
    "get_entity_history_repository",
    "get_audit_trail_repository",
    "get_compliance_query_repository",
    "get_feedback_repository",
    "get_pattern_service",
    "get_decision_service",
    "get_compliance_query_service",
    "get_audit_service",
]

