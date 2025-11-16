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
    """Detailed risk factors identified in analysis"""
    jurisdiction_risk: float = Field(ge=0, le=1, description="Risk from jurisdiction complexity")
    entity_risk: float = Field(ge=0, le=1, description="Risk from entity characteristics")
    task_risk: float = Field(ge=0, le=1, description="Risk from task characteristics")
    data_sensitivity_risk: float = Field(ge=0, le=1, description="Risk from data sensitivity")
    regulatory_risk: float = Field(ge=0, le=1, description="Risk from regulatory requirements")
    impact_risk: float = Field(ge=0, le=1, description="Risk from potential impact")
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall risk score"""
        weights = {
            'jurisdiction_risk': 0.15,
            'entity_risk': 0.15,
            'task_risk': 0.20,
            'data_sensitivity_risk': 0.20,
            'regulatory_risk': 0.20,
            'impact_risk': 0.10
        }
        
        return (
            self.jurisdiction_risk * weights['jurisdiction_risk'] +
            self.entity_risk * weights['entity_risk'] +
            self.task_risk * weights['task_risk'] +
            self.data_sensitivity_risk * weights['data_sensitivity_risk'] +
            self.regulatory_risk * weights['regulatory_risk'] +
            self.impact_risk * weights['impact_risk']
        )


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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
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

