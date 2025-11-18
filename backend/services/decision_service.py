"""
Decision Service

Business logic for compliance decision analysis.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from backend.agent.decision_engine import DecisionEngine
from backend.agent.risk_models import EntityContext, TaskContext, DecisionAnalysis
from backend.agent.proactive_suggestions import ProactiveSuggestionService
from backend.repositories.entity_history_repository import EntityHistoryRepository
from backend.repositories.compliance_query_repository import ComplianceQueryRepository
from backend.repositories.audit_trail_repository import AuditTrailRepository
from backend.db.models import EntityHistory, ComplianceQuery
from .pattern_service import PatternService
from .audit_service import AuditService


class DecisionService:
    """Service for compliance decision analysis"""
    
    def __init__(
        self,
        decision_engine: DecisionEngine,
        entity_repository: EntityHistoryRepository,
        compliance_query_repository: ComplianceQueryRepository,
        audit_trail_repository: AuditTrailRepository,
        audit_service: AuditService,
        pattern_service: PatternService
    ):
        """
        Initialize decision service.
        
        Args:
            decision_engine: Decision engine instance
            entity_repository: Repository for entity history
            compliance_query_repository: Repository for compliance queries
            audit_trail_repository: Repository for audit trail
            audit_service: Audit service
            pattern_service: Pattern analysis service
        """
        self.decision_engine = decision_engine
        self.entity_repository = entity_repository
        self.compliance_query_repository = compliance_query_repository
        self.audit_trail_repository = audit_trail_repository
        self.audit_service = audit_service
        self.pattern_service = pattern_service
    
    def analyze_decision(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> DecisionAnalysis:
        """
        Perform complete decision analysis with historical context.
        
        Args:
            entity: Entity context
            task: Task context
            
        Returns:
            DecisionAnalysis with full reasoning and historical context
        """
        # STEP 1: Analyze patterns from historical data
        pattern_result = self.pattern_service.analyze_decision_patterns(
            entity.name,
            task.category.value,
            limit=5
        )
        similar_cases = pattern_result["similar_cases"]
        pattern_analysis = pattern_result["pattern_analysis"]
        
        # STEP 2: Run decision engine analysis
        analysis = self.decision_engine.analyze_and_decide(entity, task)
        
        # STEP 3: Add historical context to analysis
        analysis.similar_cases = similar_cases
        analysis.pattern_analysis = pattern_analysis
        
        # STEP 4: Generate proactive suggestions
        has_deadline = task.regulatory_deadline is not None
        proactive_suggestions = ProactiveSuggestionService.generate_suggestions(
            db=self.entity_repository.db,  # Pass db for now (will refactor later)
            entity_name=entity.name,
            task_category=task.category.value,
            current_decision=analysis.decision.value,
            current_risk_level=analysis.risk_level.value,
            jurisdictions=entity.jurisdictions,
            has_deadline=has_deadline
        )
        analysis.proactive_suggestions = proactive_suggestions
        
        # STEP 5: Log to audit trail
        audit_entry = self.audit_service.log_decision_analysis(
            analysis=analysis,
            agent_type="decision_engine",
            metadata={
                "api_endpoint": "/decision/analyze",
                "version": "v1",
                "similar_cases_count": len(similar_cases)
            }
        )
        
        # STEP 6: Store in entity history for future queries
        history_entry = EntityHistory(
            entity_name=entity.name,
            task_category=task.category.value,
            decision=analysis.decision.value,
            risk_level=analysis.risk_level.value,
            confidence_score=analysis.confidence,
            risk_score=analysis.risk_factors.overall_score,
            task_description=task.description[:500],
            jurisdictions=entity.jurisdictions,
            meta_data={
                "audit_id": audit_entry.id,
                "has_personal_data": entity.has_personal_data,
                "is_regulated": entity.is_regulated
            }
        )
        self.entity_repository.create(history_entry)
        
        # STEP 7: Store analysis in database (legacy)
        db_query = ComplianceQuery(
            query=f"Decision Analysis: {task.description[:200]}",
            response=f"Decision: {analysis.decision.value}, Risk: {analysis.risk_level.value}",
            model="decision-engine-v1",
            status="success",
            meta_data={
                "entity_name": entity.name,
                "task_category": task.category.value,
                "risk_score": analysis.risk_factors.overall_score,
                "decision": analysis.decision.value,
                "confidence": analysis.confidence,
                "audit_id": audit_entry.id,
                "history_id": history_entry.id,
                "similar_cases_found": len(similar_cases)
            }
        )
        self.compliance_query_repository.create(db_query)
        
        return analysis
    
    def quick_risk_check(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> Dict[str, Any]:
        """
        Quick risk check without full analysis.
        
        Args:
            entity: Entity context
            task: Task context
            
        Returns:
            Simplified risk assessment
        """
        analysis = self.decision_engine.analyze_and_decide(entity, task)
        
        return {
            "risk_level": analysis.risk_level.value,
            "decision": analysis.decision.value,
            "confidence": analysis.confidence,
            "overall_risk_score": analysis.risk_factors.overall_score,
            "key_factors": {
                "jurisdiction_risk": analysis.risk_factors.jurisdiction_risk,
                "entity_risk": analysis.risk_factors.entity_risk,
                "task_risk": analysis.risk_factors.task_risk,
                "data_sensitivity_risk": analysis.risk_factors.data_sensitivity_risk,
            },
            "action_required": analysis.escalation_reason if analysis.escalation_reason else "Proceed as recommended"
        }

