"""Risk classification models and enums"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionDecision(str, Enum):
    """Decision on whether to act autonomously or escalate"""
    AUTONOMOUS = "AUTONOMOUS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ESCALATE = "ESCALATE"


class Jurisdiction(str, Enum):
    """Supported jurisdictions"""
    US_FEDERAL = "US_FEDERAL"
    US_STATE = "US_STATE"
    EU = "EU"
    UK = "UK"
    APAC = "APAC"
    CANADA = "CANADA"
    MULTI_JURISDICTIONAL = "MULTI_JURISDICTIONAL"
    UNKNOWN = "UNKNOWN"


class EntityType(str, Enum):
    """Type of business entity"""
    PUBLIC_COMPANY = "PUBLIC_COMPANY"
    PRIVATE_COMPANY = "PRIVATE_COMPANY"
    STARTUP = "STARTUP"
    NONPROFIT = "NONPROFIT"
    GOVERNMENT = "GOVERNMENT"
    HEALTHCARE = "HEALTHCARE"
    FINANCIAL_INSTITUTION = "FINANCIAL_INSTITUTION"
    UNKNOWN = "UNKNOWN"


class IndustryCategory(str, Enum):
    """Industry categories with different compliance requirements"""
    HEALTHCARE = "HEALTHCARE"
    FINANCIAL_SERVICES = "FINANCIAL_SERVICES"
    TECHNOLOGY = "TECHNOLOGY"
    RETAIL = "RETAIL"
    MANUFACTURING = "MANUFACTURING"
    EDUCATION = "EDUCATION"
    GOVERNMENT = "GOVERNMENT"
    OTHER = "OTHER"


class TaskCategory(str, Enum):
    """Categories of compliance tasks"""
    DATA_PRIVACY = "DATA_PRIVACY"
    FINANCIAL_REPORTING = "FINANCIAL_REPORTING"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    POLICY_REVIEW = "POLICY_REVIEW"
    REGULATORY_FILING = "REGULATORY_FILING"
    CONTRACT_REVIEW = "CONTRACT_REVIEW"
    INCIDENT_RESPONSE = "INCIDENT_RESPONSE"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"


class EntityContext(BaseModel):
    """Context about the entity requesting compliance guidance"""
    name: str
    entity_type: EntityType
    industry: IndustryCategory
    jurisdictions: List[Jurisdiction]
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    has_personal_data: bool = True
    is_regulated: bool = False
    previous_violations: int = 0
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TaskContext(BaseModel):
    """Context about the compliance task"""
    description: str
    category: TaskCategory
    affects_personal_data: bool = False
    affects_financial_data: bool = False
    involves_cross_border: bool = False
    regulatory_deadline: Optional[datetime] = None
    potential_impact: Optional[str] = None
    stakeholder_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Validate that task description is not empty"""
        if not v or not v.strip():
            raise ValueError('Task description cannot be empty')
        return v.strip()
    
    @field_validator('regulatory_deadline')
    @classmethod
    def normalize_deadline_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Normalize datetime to naive UTC for SQLite compatibility"""
        if v is None:
            return None
        # Convert timezone-aware datetime to naive UTC
        if v.tzinfo is not None:
            # Convert to UTC and remove timezone info
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class RiskFactors(BaseModel):
    """
    Detailed risk factors identified in analysis.
    
    Matches README description:
    - Jurisdiction: 15%
    - Entity Risk: 15%
    - Task Complexity: 20%
    - Data Sensitivity: 20%
    - Regulatory Oversight: 20%
    - Impact: 10%
    """
    jurisdiction_risk: float = Field(ge=0, le=1, description="Risk from jurisdiction complexity (15% weight)")
    entity_risk: float = Field(ge=0, le=1, description="Risk from entity characteristics (15% weight)")
    task_risk: float = Field(ge=0, le=1, description="Risk from task complexity (20% weight)")
    data_sensitivity_risk: float = Field(ge=0, le=1, description="Risk from data sensitivity (20% weight)")
    regulatory_risk: float = Field(ge=0, le=1, description="Risk from regulatory oversight (20% weight)")
    impact_risk: float = Field(ge=0, le=1, description="Risk from potential impact (10% weight)")
    
    @property
    def overall_score(self) -> float:
        """
        Calculate weighted overall risk score.
        
        Weights match README specification:
        - Jurisdiction: 15%
        - Entity Risk: 15%
        - Task Complexity: 20%
        - Data Sensitivity: 20%
        - Regulatory Oversight: 20%
        - Impact: 10%
        """
        weights = {
            'jurisdiction_risk': 0.15,      # 15%
            'entity_risk': 0.15,            # 15%
            'task_risk': 0.20,              # 20% (Task Complexity)
            'data_sensitivity_risk': 0.20,  # 20%
            'regulatory_risk': 0.20,         # 20% (Regulatory Oversight)
            'impact_risk': 0.10             # 10%
        }
        
        return (
            self.jurisdiction_risk * weights['jurisdiction_risk'] +
            self.entity_risk * weights['entity_risk'] +
            self.task_risk * weights['task_risk'] +
            self.data_sensitivity_risk * weights['data_sensitivity_risk'] +
            self.regulatory_risk * weights['regulatory_risk'] +
            self.impact_risk * weights['impact_risk']
        )
    
    def classify_risk(self) -> RiskLevel:
        """
        Classify risk level based on overall score.
        
        Returns:
            RiskLevel (LOW, MEDIUM, or HIGH)
        """
        score = self.overall_score
        
        if score < 0.35:
            return RiskLevel.LOW
        elif score < 0.65:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def generate_rationale(self) -> List[str]:
        """
        Generate detailed rationale for the risk assessment.
        
        Returns:
            List of rationale strings explaining each factor
        """
        rationale = []
        
        # Jurisdiction (15%)
        if self.jurisdiction_risk >= 0.7:
            rationale.append(
                f"🌍 Jurisdiction Complexity (15%): HIGH ({self.jurisdiction_risk:.2f}) - "
                "Multi-regulatory framework or complex jurisdiction requirements"
            )
        elif self.jurisdiction_risk >= 0.4:
            rationale.append(
                f"🌍 Jurisdiction Complexity (15%): MEDIUM ({self.jurisdiction_risk:.2f}) - "
                "Moderate regulatory complexity"
            )
        else:
            rationale.append(
                f"🌍 Jurisdiction Complexity (15%): LOW ({self.jurisdiction_risk:.2f}) - "
                "Standard jurisdiction requirements"
            )
        
        # Entity Risk (15%)
        if self.entity_risk >= 0.7:
            rationale.append(
                f"🏢 Entity Risk Profile (15%): HIGH ({self.entity_risk:.2f}) - "
                "High-risk entity type, industry, or violation history"
            )
        elif self.entity_risk >= 0.4:
            rationale.append(
                f"🏢 Entity Risk Profile (15%): MEDIUM ({self.entity_risk:.2f}) - "
                "Moderate entity risk factors"
            )
        else:
            rationale.append(
                f"🏢 Entity Risk Profile (15%): LOW ({self.entity_risk:.2f}) - "
                "Low-risk entity profile"
            )
        
        # Task Complexity (20%)
        if self.task_risk >= 0.7:
            rationale.append(
                f"📋 Task Complexity (20%): HIGH ({self.task_risk:.2f}) - "
                "Complex task category (e.g., regulatory filing, incident response)"
            )
        elif self.task_risk >= 0.4:
            rationale.append(
                f"📋 Task Complexity (20%): MEDIUM ({self.task_risk:.2f}) - "
                "Moderate task complexity"
            )
        else:
            rationale.append(
                f"📋 Task Complexity (20%): LOW ({self.task_risk:.2f}) - "
                "Simple task category (e.g., general inquiry)"
            )
        
        # Data Sensitivity (20%)
        if self.data_sensitivity_risk >= 0.7:
            rationale.append(
                f"🔐 Data Sensitivity (20%): HIGH ({self.data_sensitivity_risk:.2f}) - "
                "Involves personal data, financial data, or sensitive information"
            )
        elif self.data_sensitivity_risk >= 0.4:
            rationale.append(
                f"🔐 Data Sensitivity (20%): MEDIUM ({self.data_sensitivity_risk:.2f}) - "
                "Some sensitive data involved"
            )
        else:
            rationale.append(
                f"🔐 Data Sensitivity (20%): LOW ({self.data_sensitivity_risk:.2f}) - "
                "No sensitive data indicated"
            )
        
        # Regulatory Oversight (20%)
        if self.regulatory_risk >= 0.7:
            rationale.append(
                f"⚖️ Regulatory Oversight (20%): HIGH ({self.regulatory_risk:.2f}) - "
                "Multiple regulations apply, directly regulated entity, or filing required"
            )
        elif self.regulatory_risk >= 0.4:
            rationale.append(
                f"⚖️ Regulatory Oversight (20%): MEDIUM ({self.regulatory_risk:.2f}) - "
                "Some regulatory requirements apply"
            )
        else:
            rationale.append(
                f"⚖️ Regulatory Oversight (20%): LOW ({self.regulatory_risk:.2f}) - "
                "Minimal regulatory compliance risk"
            )
        
        # Impact (10%)
        if self.impact_risk >= 0.7:
            rationale.append(
                f"💥 Impact Severity (10%): HIGH ({self.impact_risk:.2f}) - "
                "High stakeholder impact or severe consequences"
            )
        elif self.impact_risk >= 0.4:
            rationale.append(
                f"💥 Impact Severity (10%): MEDIUM ({self.impact_risk:.2f}) - "
                "Moderate impact potential"
            )
        else:
            rationale.append(
                f"💥 Impact Severity (10%): LOW ({self.impact_risk:.2f}) - "
                "Low impact scenario"
            )
        
        # Overall summary
        overall_score = self.overall_score
        risk_level = self.classify_risk()
        rationale.append(
            f"\n📊 OVERALL RISK SCORE: {overall_score:.3f} ({risk_level.value})"
        )
        rationale.append(
            f"   Weighted calculation: "
            f"({self.jurisdiction_risk:.2f} × 0.15) + "
            f"({self.entity_risk:.2f} × 0.15) + "
            f"({self.task_risk:.2f} × 0.20) + "
            f"({self.data_sensitivity_risk:.2f} × 0.20) + "
            f"({self.regulatory_risk:.2f} × 0.20) + "
            f"({self.impact_risk:.2f} × 0.10) = {overall_score:.3f}"
        )
        
        return rationale


class DecisionAnalysis(BaseModel):
    """Complete decision analysis output"""
    entity_context: EntityContext
    task_context: TaskContext
    risk_factors: RiskFactors
    risk_level: RiskLevel
    decision: ActionDecision
    confidence: float = Field(ge=0, le=1, description="Confidence in the decision")
    reasoning: List[str] = Field(description="Step-by-step reasoning for the decision")
    recommendations: List[str] = Field(description="Recommended actions")
    escalation_reason: Optional[str] = None
    similar_cases: Optional[List[dict]] = Field(default=None, description="Similar past cases for this organization")
    pattern_analysis: Optional[str] = Field(default=None, description="Analysis of historical patterns")
    proactive_suggestions: Optional[List[dict]] = Field(default=None, description="Proactive suggestions and insights")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "risk_level": "MEDIUM",
                "decision": "REVIEW_REQUIRED",
                "confidence": 0.85,
                "reasoning": [
                    "Entity operates in EU jurisdiction (GDPR applies)",
                    "Task involves personal data processing",
                    "Medium-sized company with adequate resources"
                ],
                "recommendations": [
                    "Have legal team review before implementation",
                    "Document decision rationale"
                ]
            }
        }


def assess_risk(
    jurisdiction_risk: float,
    entity_risk: float,
    task_complexity: float,
    data_sensitivity: float,
    regulatory_oversight: float,
    impact: float
) -> Dict[str, Any]:
    """
    Assess risk using the 6-factor model matching README description.
    
    Args:
        jurisdiction_risk: Jurisdiction complexity risk (0.0 to 1.0)
        entity_risk: Entity risk profile (0.0 to 1.0)
        task_complexity: Task complexity risk (0.0 to 1.0)
        data_sensitivity: Data sensitivity risk (0.0 to 1.0)
        regulatory_oversight: Regulatory oversight risk (0.0 to 1.0)
        impact: Impact severity risk (0.0 to 1.0)
    
    Returns:
        Dictionary containing:
            - score: Overall risk score (0.0 to 1.0)
            - classification: Risk level (LOW, MEDIUM, HIGH)
            - rationale: List of rationale strings
            - factors: Individual factor scores with weights
    """
    # Create RiskFactors instance
    risk_factors = RiskFactors(
        jurisdiction_risk=jurisdiction_risk,
        entity_risk=entity_risk,
        task_risk=task_complexity,
        data_sensitivity_risk=data_sensitivity,
        regulatory_risk=regulatory_oversight,
        impact_risk=impact
    )
    
    # Calculate score
    score = risk_factors.overall_score
    
    # Classify
    classification = risk_factors.classify_risk()
    
    # Generate rationale
    rationale = risk_factors.generate_rationale()
    
    return {
        "score": round(score, 3),
        "classification": classification.value,
        "rationale": rationale,
        "factors": {
            "jurisdiction": {
                "score": jurisdiction_risk,
                "weight": 0.15,
                "weighted_contribution": round(jurisdiction_risk * 0.15, 3)
            },
            "entity_risk": {
                "score": entity_risk,
                "weight": 0.15,
                "weighted_contribution": round(entity_risk * 0.15, 3)
            },
            "task_complexity": {
                "score": task_complexity,
                "weight": 0.20,
                "weighted_contribution": round(task_complexity * 0.20, 3)
            },
            "data_sensitivity": {
                "score": data_sensitivity,
                "weight": 0.20,
                "weighted_contribution": round(data_sensitivity * 0.20, 3)
            },
            "regulatory_oversight": {
                "score": regulatory_oversight,
                "weight": 0.20,
                "weighted_contribution": round(regulatory_oversight * 0.20, 3)
            },
            "impact": {
                "score": impact,
                "weight": 0.10,
                "weighted_contribution": round(impact * 0.10, 3)
            }
        }
    }
