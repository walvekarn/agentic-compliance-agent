"""
Schema Converter
================
Converts backend models to unified schema formats.
"""

from typing import Dict, Any, List
from backend.agent.risk_models import DecisionAnalysis, RiskFactors
from shared.schemas.analysis_result import (
    AnalysisResult,
    RiskAnalysisItem,
    WhyReasoning,
    DecisionOutcome,
    RiskLevel
)


def convert_decision_analysis_to_analysis_result(
    analysis: DecisionAnalysis,
    detailed: bool = True
) -> Dict[str, Any]:
    """
    Convert DecisionAnalysis to unified AnalysisResult schema format.
    
    Args:
        analysis: DecisionAnalysis object from decision engine
        detailed: If True, include all optional fields. If False, simple view.
        
    Returns:
        Dictionary matching AnalysisResult schema exactly
    """
    # Convert risk factors to risk_analysis items
    risk_factors = analysis.risk_factors
    risk_analysis_items = [
        RiskAnalysisItem(
            factor="jurisdiction_risk",
            score=risk_factors.jurisdiction_risk,
            weight=0.15,
            explanation=f"Jurisdiction complexity risk: {risk_factors.jurisdiction_risk:.2f}"
        ),
        RiskAnalysisItem(
            factor="entity_risk",
            score=risk_factors.entity_risk,
            weight=0.15,
            explanation=f"Entity risk profile: {risk_factors.entity_risk:.2f}"
        ),
        RiskAnalysisItem(
            factor="task_risk",
            score=risk_factors.task_risk,
            weight=0.20,
            explanation=f"Task complexity risk: {risk_factors.task_risk:.2f}"
        ),
        RiskAnalysisItem(
            factor="data_sensitivity_risk",
            score=risk_factors.data_sensitivity_risk,
            weight=0.20,
            explanation=f"Data sensitivity risk: {risk_factors.data_sensitivity_risk:.2f}"
        ),
        RiskAnalysisItem(
            factor="regulatory_risk",
            score=risk_factors.regulatory_risk,
            weight=0.20,
            explanation=f"Regulatory oversight risk: {risk_factors.regulatory_risk:.2f}"
        ),
        RiskAnalysisItem(
            factor="impact_risk",
            score=risk_factors.impact_risk,
            weight=0.10,
            explanation=f"Impact severity risk: {risk_factors.impact_risk:.2f}"
        ),
    ]
    
    # Convert decision outcome
    decision_outcome = DecisionOutcome(analysis.decision.value)
    
    # Convert risk level
    risk_level = RiskLevel(analysis.risk_level.value)
    
    # Create why reasoning
    why_reasoning = WhyReasoning(
        reasoning_steps=analysis.reasoning,
        confidence_factors=None,  # Can be added if available
        uncertainty_notes=None    # Can be added if available
    )
    
    # Create AnalysisResult
    analysis_result = AnalysisResult(
        decision=decision_outcome,
        confidence=analysis.confidence,
        risk_level=risk_level,
        risk_score=risk_factors.overall_score,
        risk_analysis=risk_analysis_items,
        why=why_reasoning,
        recommendations=analysis.recommendations,
        escalation_reason=analysis.escalation_reason,
        similar_cases=analysis.similar_cases,
        pattern_analysis=analysis.pattern_analysis,
        proactive_suggestions=analysis.proactive_suggestions,
        timestamp=analysis.timestamp
    )
    
    # Convert to dict using appropriate method
    if detailed:
        return analysis_result.to_detailed_dict()
    else:
        return analysis_result.to_simple_dict()


def ensure_required_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all required fields are present in response.
    Removes empty fields and redundant keys.
    
    Args:
        data: Response dictionary
        
    Returns:
        Cleaned dictionary with all required fields
    """
    # Required fields from AnalysisResult schema
    required_fields = {
        "decision": None,
        "confidence": None,
        "risk_level": None,
        "risk_score": 0.0,
        "risk_analysis": [],
        "why": {
            "reasoning_steps": []
        }
    }
    
    # Start with required structure
    result = {}
    
    # Ensure decision is present
    result["decision"] = data.get("decision") or data.get("decision_outcome") or "REVIEW_REQUIRED"
    
    # Ensure confidence is present (0-1 range) - use None if not present, never default to 0.0
    confidence = data.get("confidence") or data.get("confidence_score")
    if confidence is not None:
        if confidence > 1.0:
            confidence = confidence / 100.0
        result["confidence"] = max(0.0, min(1.0, float(confidence)))
    else:
        result["confidence"] = None  # Use None when not present, not 0.0
    
    # Ensure risk_level is present
    result["risk_level"] = data.get("risk_level") or data.get("risk_level", "MEDIUM")
    
    # Ensure risk_analysis is present
    if "risk_analysis" in data and isinstance(data["risk_analysis"], list) and len(data["risk_analysis"]) > 0:
        result["risk_analysis"] = data["risk_analysis"]
    else:
        result["risk_analysis"] = []

    # Ensure risk_score is present (prefers explicit value)
    result["risk_score"] = data.get("risk_score") if data.get("risk_score") is not None else 0.0
    
    # Ensure why.reasoning_steps is present
    if "why" in data and isinstance(data["why"], dict):
        result["why"] = data["why"]
        if "reasoning_steps" not in result["why"]:
            result["why"]["reasoning_steps"] = []
    else:
        result["why"] = {"reasoning_steps": []}
    
    # Add optional fields only if they have values
    if data.get("recommendations"):
        result["recommendations"] = data["recommendations"]
    if data.get("escalation_reason"):
        result["escalation_reason"] = data["escalation_reason"]
    if data.get("similar_cases"):
        result["similar_cases"] = data["similar_cases"]
    if data.get("pattern_analysis"):
        result["pattern_analysis"] = data["pattern_analysis"]
    if data.get("proactive_suggestions"):
        result["proactive_suggestions"] = data["proactive_suggestions"]
    if data.get("timestamp"):
        result["timestamp"] = data["timestamp"]
    
    return result
