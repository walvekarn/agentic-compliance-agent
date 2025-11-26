"""
Unified Analysis Result Schema
===============================
Standardized response format for all compliance analysis requests.

Backend returns exactly:
{
    "decision": "AUTONOMOUS" | "REVIEW_REQUIRED" | "ESCALATE",
    "confidence": float (0-1),
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "risk_analysis": [...],
    "why": {
        "reasoning_steps": [...]
    }
}
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DecisionOutcome(str, Enum):
    """Decision outcome types"""
    AUTONOMOUS = "AUTONOMOUS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ESCALATE = "ESCALATE"


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskAnalysisItem(BaseModel):
    """Single risk analysis item"""
    factor: str = Field(description="Risk factor name")
    score: float = Field(ge=0, le=1, description="Risk score (0-1)")
    weight: float = Field(ge=0, le=1, description="Weight in overall calculation")
    explanation: str = Field(description="Explanation of this risk factor")


class RiskAnalysis(BaseModel):
    """Complete risk analysis"""
    overall_score: float = Field(ge=0, le=1, description="Overall risk score (0-1)")
    risk_level: RiskLevel = Field(description="Classified risk level")
    factors: List[RiskAnalysisItem] = Field(description="Individual risk factors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 0.65,
                "risk_level": "MEDIUM",
                "factors": [
                    {
                        "factor": "jurisdiction_risk",
                        "score": 0.7,
                        "weight": 0.15,
                        "explanation": "Multi-jurisdictional complexity"
                    }
                ]
            }
        }


class WhyReasoning(BaseModel):
    """Reasoning chain explaining the decision"""
    reasoning_steps: List[str] = Field(description="Step-by-step reasoning chain")
    confidence_factors: Optional[List[str]] = Field(
        default=None,
        description="Factors contributing to confidence level"
    )
    uncertainty_notes: Optional[List[str]] = Field(
        default=None,
        description="Areas of uncertainty or limitations"
    )


class AnalysisResult(BaseModel):
    """
    Unified analysis result schema.
    
    This is the standard response format for all compliance analysis requests.
    Both simple and detailed views use this structure, with detailed views
    containing more complete reasoning_steps and risk_analysis.
    """
    decision: DecisionOutcome = Field(description="Final decision outcome")
    confidence: float = Field(ge=0, le=1, description="Confidence in decision (0-1)")
    risk_level: RiskLevel = Field(description="Classified risk level")
    risk_analysis: List[RiskAnalysisItem] = Field(
        description="Risk analysis breakdown"
    )
    risk_score: float = Field(ge=0, le=1, description="Weighted risk score (0-1)")
    why: WhyReasoning = Field(description="Reasoning chain explaining the decision")
    
    # Optional fields for detailed views
    recommendations: Optional[List[str]] = Field(
        default=None,
        description="Recommended actions"
    )
    escalation_reason: Optional[str] = Field(
        default=None,
        description="Reason for escalation if applicable"
    )
    similar_cases: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Similar past cases"
    )
    pattern_analysis: Optional[str] = Field(
        default=None,
        description="Analysis of historical patterns"
    )
    proactive_suggestions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Proactive suggestions and insights"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="Timestamp of analysis"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "decision": "REVIEW_REQUIRED",
                "confidence": 0.85,
                "risk_level": "MEDIUM",
            "risk_analysis": [
                {
                    "factor": "jurisdiction_risk",
                    "score": 0.7,
                    "weight": 0.15,
                    "explanation": "Multi-jurisdictional complexity"
                }
            ],
            "risk_score": 0.65,
            "why": {
                "reasoning_steps": [
                    "Entity operates in EU jurisdiction (GDPR applies)",
                    "Task involves personal data processing",
                    "Medium-sized company with adequate resources"
                ]
            }
        }
    }
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """Convert to simple view (summary only)"""
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "risk_analysis": [
                {
                    "factor": item.factor,
                    "score": item.score,
                    "weight": item.weight,
                    "explanation": item.explanation
                }
                for item in self.risk_analysis
            ],
            "why": {
                "reasoning_steps": self.why.reasoning_steps[:3]  # First 3 steps only
            }
        }
    
    def to_detailed_dict(self) -> Dict[str, Any]:
        """Convert to detailed view (full reasoning, full risk, chain of thought)"""
        result = {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "risk_analysis": [
                {
                    "factor": item.factor,
                    "score": item.score,
                    "weight": item.weight,
                    "explanation": item.explanation
                }
                for item in self.risk_analysis
            ],
            "why": {
                "reasoning_steps": self.why.reasoning_steps,
                "confidence_factors": self.why.confidence_factors,
                "uncertainty_notes": self.why.uncertainty_notes
            },
            "timestamp": self.timestamp.isoformat()
        }
        
        # Add optional fields if present
        if self.recommendations:
            result["recommendations"] = self.recommendations
        if self.escalation_reason:
            result["escalation_reason"] = self.escalation_reason
        if self.similar_cases:
            result["similar_cases"] = self.similar_cases
        if self.pattern_analysis:
            result["pattern_analysis"] = self.pattern_analysis
        if self.proactive_suggestions:
            result["proactive_suggestions"] = self.proactive_suggestions
        
        return result
