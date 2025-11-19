"""API routes for compliance decision engine"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from backend.agent.decision_engine import DecisionEngine
from backend.agent.audit_service import AuditService
from backend.agent.proactive_suggestions import ProactiveSuggestionService
from backend.agent.what_if_engine import WhatIfEngine
from backend.agent.risk_models import (
    EntityContext,
    TaskContext,
    DecisionAnalysis,
    # Unused direct enums removed to reduce lints
)
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.db.base import get_db
from backend.auth.security import get_current_user
from backend.db.models import ComplianceQuery, EntityHistory
from backend.api.rate_limit import limiter, AUTH_RATE

router = APIRouter(prefix="/decision", tags=["Decision Engine", "Protected"], dependencies=[Depends(get_current_user)])

# Initialize decision engine and what-if engine
decision_engine = DecisionEngine()
what_if_engine = WhatIfEngine(decision_engine)


@router.post("/analyze", response_model=DecisionAnalysis)
@limiter.limit(AUTH_RATE)
async def analyze_compliance_decision(
    request: Request,
    entity: EntityContext,
    task: TaskContext,
    db: Session = Depends(get_db)
):
    """
    Analyze compliance task and determine autonomous action vs escalation
    
    This endpoint:
    1. Retrieves similar past cases for contextual awareness
    2. Analyzes entity characteristics and jurisdiction
    3. Classifies task risk (LOW/MEDIUM/HIGH)
    4. Returns decision (AUTONOMOUS/REVIEW_REQUIRED/ESCALATE) with reasoning
    5. Stores decision in entity history for future reference
    
    Args:
        entity: Entity context (company info, jurisdiction, industry)
        task: Task context (description, category, data sensitivity)
        db: Database session
        
    Returns:
        DecisionAnalysis with complete risk assessment, decision, and historical context
    """
    try:
        # STEP 1: Query similar past cases (entity memory)
        similar_cases_query = db.query(EntityHistory).filter(
            EntityHistory.entity_name == entity.name,
            EntityHistory.task_category == task.category.value
        ).order_by(EntityHistory.timestamp.desc()).limit(5).all()
        
        # Convert to dict for response
        similar_cases = [case.to_dict() for case in similar_cases_query]
        
        # Generate pattern analysis
        pattern_analysis = None
        if similar_cases:
            total_cases = len(similar_cases)
            autonomous_count = sum(1 for c in similar_cases if c['decision'] == 'AUTONOMOUS')
            review_count = sum(1 for c in similar_cases if c['decision'] == 'REVIEW_REQUIRED')
            escalate_count = sum(1 for c in similar_cases if c['decision'] == 'ESCALATE')
            
            # Calculate percentages
            autonomous_pct = (autonomous_count / total_cases * 100) if total_cases > 0 else 0
            review_pct = (review_count / total_cases * 100) if total_cases > 0 else 0
            escalate_pct = (escalate_count / total_cases * 100) if total_cases > 0 else 0
            
            # Generate narrative
            pattern_parts = []
            pattern_parts.append(f"Based on {total_cases} similar past {'case' if total_cases == 1 else 'cases'} for {entity.name}:")
            
            if escalate_count > 0:
                pattern_parts.append(f"escalated {escalate_pct:.0f}% of the time")
            if review_count > 0:
                pattern_parts.append(f"required review {review_pct:.0f}% of the time")
            if autonomous_count > 0:
                pattern_parts.append(f"handled autonomously {autonomous_pct:.0f}% of the time")
            
            # Average confidence
            avg_confidence = sum(c.get('confidence_score', 0) or 0 for c in similar_cases) / total_cases
            pattern_parts.append(f"Average confidence in past decisions: {avg_confidence*100:.0f}%")
            
            pattern_analysis = ". ".join(pattern_parts) + "."
        
        # STEP 2: Run decision engine analysis
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # STEP 3: Add historical context to analysis
        analysis.similar_cases = similar_cases
        analysis.pattern_analysis = pattern_analysis
        
        # STEP 3.5: Generate proactive suggestions
        has_deadline = task.regulatory_deadline is not None
        proactive_suggestions = ProactiveSuggestionService.generate_suggestions(
            db=db,
            entity_name=entity.name,
            task_category=task.category.value,
            current_decision=analysis.decision.value,
            current_risk_level=analysis.risk_level.value,
            jurisdictions=entity.jurisdictions,
            has_deadline=has_deadline
        )
        analysis.proactive_suggestions = proactive_suggestions
        
        # STEP 4: Log to audit trail
        audit_entry = AuditService.log_decision_analysis(
            db=db,
            analysis=analysis,
            agent_type="decision_engine",
            metadata={
                "api_endpoint": "/decision/analyze",
                "version": "v1",
                "similar_cases_count": len(similar_cases)
            }
        )
        
        # STEP 5: Store in entity history for future queries
        history_entry = EntityHistory(
            entity_name=entity.name,
            task_category=task.category.value,
            decision=analysis.decision.value,
            risk_level=analysis.risk_level.value,
            confidence_score=analysis.confidence,
            risk_score=analysis.risk_factors.overall_score,
            task_description=task.description[:500],  # Truncate long descriptions
            jurisdictions=entity.jurisdictions,
            meta_data={
                "audit_id": audit_entry.id,
                "has_personal_data": entity.has_personal_data,
                "is_regulated": entity.is_regulated
            }
        )
        db.add(history_entry)
        
        # STEP 6: Store analysis in database (legacy)
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
        db.add(db_query)
        db.commit()
        
        return analysis
        
    except Exception as e:
        db.rollback()
        from backend.api.error_utils import raise_standardized_error
        raise_standardized_error(
            status_code=500,
            error_type="AnalysisError",
            message=f"Analysis failed: {str(e)}",
            details={"error_type": type(e).__name__}
        )


@router.post("/quick-check")
async def quick_risk_check(
    entity: EntityContext,
    task: TaskContext
) -> dict:
    """
    Quick risk check without full analysis (faster endpoint)
    
    Returns:
        Simplified risk assessment with key metrics
    """
    try:
        analysis = decision_engine.analyze_and_decide(entity, task)
        
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
        
    except Exception as e:
        from backend.api.error_utils import raise_standardized_error
        raise_standardized_error(
            status_code=500,
            error_type="QuickCheckError",
            message=f"Quick check failed: {str(e)}",
            details={"error_type": type(e).__name__}
        )


@router.get("/risk-levels")
async def get_risk_level_info():
    """
    Get information about risk level classifications
    
    Returns:
        Risk level definitions and thresholds
    """
    return {
        "risk_levels": {
            "LOW": {
                "threshold": "< 0.35",
                "description": "Low risk - may proceed with autonomous action if entity is capable",
                "typical_action": "AUTONOMOUS or REVIEW_REQUIRED"
            },
            "MEDIUM": {
                "threshold": "0.35 - 0.65",
                "description": "Medium risk - human review required before action",
                "typical_action": "REVIEW_REQUIRED"
            },
            "HIGH": {
                "threshold": "> 0.65",
                "description": "High risk - escalate to compliance specialist",
                "typical_action": "ESCALATE"
            }
        },
        "decisions": {
            "AUTONOMOUS": "Agent can take action independently",
            "REVIEW_REQUIRED": "Human review needed before proceeding",
            "ESCALATE": "Must involve compliance specialist or legal counsel"
        },
        "risk_factors": {
            "jurisdiction_risk": "Complexity of regulatory jurisdiction(s)",
            "entity_risk": "Entity characteristics and compliance history",
            "task_risk": "Task category and complexity",
            "data_sensitivity_risk": "Sensitivity of data involved",
            "regulatory_risk": "Number and stringency of applicable regulations",
            "impact_risk": "Potential impact of errors or non-compliance"
        }
    }


@router.post("/batch-analyze")
async def batch_analyze(
    entity: EntityContext,
    tasks: List[TaskContext],
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Analyze multiple tasks for the same entity
    
    Args:
        entity: Entity context
        tasks: List of task contexts to analyze
        db: Database session
        
    Returns:
        List of simplified decision analyses
    """
    try:
        results = []
        audit_ids = []
        
        for task in tasks:
            analysis = decision_engine.analyze_and_decide(entity, task)
            
            # Log each decision to audit trail
            audit_entry = AuditService.log_decision_analysis(
                db=db,
                analysis=analysis,
                agent_type="decision_engine",
                metadata={
                    "api_endpoint": "/decision/batch-analyze",
                    "version": "v1",
                    "batch_processing": True
                }
            )
            audit_ids.append(audit_entry.id)
            
            results.append({
                "task_description": task.description,
                "task_category": task.category.value,
                "risk_level": analysis.risk_level.value,
                "decision": analysis.decision.value,
                "confidence": analysis.confidence,
                "risk_score": analysis.risk_factors.overall_score,
                "escalation_reason": analysis.escalation_reason,
                "audit_id": audit_entry.id
            })
        
        # Store batch analysis
        db_query = ComplianceQuery(
            query=f"Batch Analysis: {len(tasks)} tasks for {entity.name}",
            response=f"Processed {len(results)} tasks",
            model="decision-engine-v1",
            status="success",
            meta_data={
                "entity": entity.name,
                "task_count": len(tasks),
                "audit_ids": audit_ids
            }
        )
        db.add(db_query)
        db.commit()
        
        return results
        
    except Exception as e:
        db.rollback()
        from backend.api.error_utils import raise_standardized_error
        raise_standardized_error(
            status_code=500,
            error_type="BatchAnalysisError",
            message=f"Batch analysis failed: {str(e)}",
            details={"error_type": type(e).__name__, "task_count": len(tasks) if 'tasks' in locals() else None}
        )


class WhatIfRequest(BaseModel):
    """Request model for what-if scenario analysis"""
    baseline: DecisionAnalysis
    changes: Dict[str, Any] = Field(
        description="Dictionary of changes to apply. Keys can be: "
        "jurisdiction_risk, entity_risk, task_risk, data_sensitivity_risk, "
        "regulatory_risk, impact_risk (all floats 0.0-1.0), or entity, task (context objects)"
    )


@router.post("/what-if")
@limiter.limit(AUTH_RATE)
async def what_if_analysis(
    request: Request,
    req: WhatIfRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform what-if scenario analysis.
    
    Simulates changes to risk factors and shows:
    - Changed input
    - New score
    - Explanation
    - Factor deltas
    - Decision change (if any)
    
    Args:
        request: FastAPI Request object (for rate limiting)
        req: WhatIfRequest containing baseline DecisionAnalysis and changes
        db: Database session
    
    Returns:
        Dictionary with scenario analysis results
    """
    try:
        result = what_if_engine.analyze_scenario(
            baseline=req.baseline,
            changes=req.changes
        )
        
        # Log what-if analysis to audit trail
        AuditService.log_custom_decision(
            db=db,
            entity_name=req.baseline.entity_context.name,
            task_category=req.baseline.task_context.category.value,
            decision="WHAT_IF_ANALYSIS",
            risk_level=result["new_level"],
            confidence=0.8,
            reasoning=result["explanation"],
            metadata={
                "api_endpoint": "/decision/what-if",
                "baseline_score": result["baseline_score"],
                "new_score": result["new_score"],
                "score_delta": result["score_delta"],
                "decision_changed": result["decision_change"]["changed"],
                "changes": req.changes
            }
        )
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"What-if analysis failed: {str(e)}")


class CompareScenariosRequest(BaseModel):
    """Request model for comparing multiple scenarios"""
    baseline: DecisionAnalysis
    scenarios: List[Dict[str, Any]] = Field(
        description="List of scenario change dictionaries to compare"
    )


@router.post("/what-if/compare")
@limiter.limit(AUTH_RATE)
async def compare_scenarios(
    request: Request,
    req: CompareScenariosRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare multiple what-if scenarios against a baseline.
    
    Args:
        request: FastAPI Request object (for rate limiting)
        req: CompareScenariosRequest with baseline and list of scenarios
        db: Database session
    
    Returns:
        Dictionary with baseline and all scenario comparisons
    """
    try:
        result = what_if_engine.compare_scenarios(
            baseline=req.baseline,
            scenarios=req.scenarios
        )
        
        # Log comparison to audit trail
        AuditService.log_custom_decision(
            db=db,
            entity_name=req.baseline.entity_context.name,
            task_category=req.baseline.task_context.category.value,
            decision="SCENARIO_COMPARISON",
            risk_level=req.baseline.risk_level,
            confidence=0.8,
            reasoning=[f"Compared {len(req.scenarios)} scenarios"],
            metadata={
                "api_endpoint": "/decision/what-if/compare",
                "scenario_count": len(req.scenarios),
                "baseline_score": req.baseline.risk_factors.overall_score
            }
        )
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Scenario comparison failed: {str(e)}")


class TriggerCheckRequest(BaseModel):
    """Request model for checking proactive suggestion triggers"""
    entity_name: str = Field(description="Organization name")
    task_category: Optional[str] = Field(default=None, description="Optional task category filter")


@router.post("/triggers/check")
@limiter.limit(AUTH_RATE)
async def check_triggers(
    request: Request,
    req: TriggerCheckRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check all proactive suggestion triggers.
    
    Triggers checked:
    - Deadlines: Upcoming regulatory deadlines
    - Risk Trends: Rising risk patterns
    - Violations: Previous compliance violations
    - Multiple Incidents: Recurring incidents
    - Regulatory Patterns: Regulatory changes or patterns
    
    Args:
        request: FastAPI Request object (for rate limiting)
        req: TriggerCheckRequest with entity name and optional task category
        db: Database session
    
    Returns:
        Dictionary with list of suggestion objects grouped by trigger type
    """
    try:
        suggestions = ProactiveSuggestionService.check_triggers(
            db=db,
            entity_name=req.entity_name,
            task_category=req.task_category
        )
        
        # Group suggestions by trigger type
        grouped = {}
        for suggestion in suggestions:
            trigger = suggestion.get("trigger", "unknown")
            if trigger not in grouped:
                grouped[trigger] = []
            grouped[trigger].append(suggestion)
        
        # Log trigger check to audit trail
        AuditService.log_custom_decision(
            db=db,
            entity_name=req.entity_name,
            task_category=req.task_category or "GENERAL",
            decision="TRIGGER_CHECK",
            risk_level="LOW",
            confidence=0.8,
            reasoning=[f"Checked {len(suggestions)} trigger(s) across {len(grouped)} trigger type(s)"],
            metadata={
                "api_endpoint": "/decision/triggers/check",
                "suggestion_count": len(suggestions),
                "trigger_types": list(grouped.keys())
            }
        )
        db.commit()
        
        return {
            "entity_name": req.entity_name,
            "task_category": req.task_category,
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
            "grouped_by_trigger": grouped,
            "trigger_summary": {
                trigger: len(suggestions_list)
                for trigger, suggestions_list in grouped.items()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Trigger check failed: {str(e)}")

