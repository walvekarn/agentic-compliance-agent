"""API routes for entity analysis and audit log retrieval"""

from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from backend.agent.decision_engine import DecisionEngine
from backend.agent.audit_service import AuditService
from backend.agent.risk_models import (
    EntityContext,
    TaskContext,
    EntityType,
    IndustryCategory,
    Jurisdiction,
    TaskCategory
)
from backend.db.base import get_db
from backend.auth.security import get_current_user

router = APIRouter(tags=["Entity Analysis", "Protected"], dependencies=[Depends(get_current_user)])


# Request/Response Models
class AnalyzeEntityRequest(BaseModel):
    """Request model for entity analysis"""
    entity_name: str = Field(..., description="Name of the entity to analyze")
    locations: List[str] = Field(..., description="List of locations/jurisdictions (e.g., ['US', 'EU', 'UK'])")
    entity_type: Optional[str] = Field(default="PRIVATE_COMPANY", description="Type of entity")
    industry: Optional[str] = Field(default="TECHNOLOGY", description="Industry category")
    employee_count: Optional[int] = Field(default=None, description="Number of employees")
    annual_revenue: Optional[float] = Field(default=None, description="Annual revenue")
    has_personal_data: bool = Field(default=True, description="Whether entity handles personal data")
    is_regulated: bool = Field(default=False, description="Whether entity is directly regulated")
    previous_violations: int = Field(default=0, description="Number of previous compliance violations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "TechCorp Inc",
                "locations": ["US", "EU", "UK"],
                "entity_type": "PRIVATE_COMPANY",
                "industry": "TECHNOLOGY",
                "employee_count": 250,
                "has_personal_data": True
            }
        }


class ComplianceTask(BaseModel):
    """Individual compliance task in the calendar"""
    task_id: str
    task_name: str
    description: str
    category: str
    deadline: Optional[str]
    frequency: str  # "annual", "quarterly", "monthly", "one-time", "as-needed"
    decision: str  # AUTONOMOUS, REVIEW_REQUIRED, ESCALATE
    confidence: float
    risk_level: str
    reasoning_summary: str
    audit_id: Optional[int]


class ComplianceCalendar(BaseModel):
    """Compliance calendar with scheduled tasks"""
    entity_name: str
    jurisdictions: List[str]
    applicable_regulations: List[str]
    tasks: List[ComplianceTask]
    summary: Dict[str, Any]


class AuditLogResponse(BaseModel):
    """Response model for audit log retrieval"""
    task_id: str
    audit_id: int
    timestamp: str
    entity_name: Optional[str]
    task_description: str
    task_category: Optional[str]
    decision_outcome: str
    confidence_score: float
    risk_level: Optional[str]
    risk_score: Optional[float]
    reasoning_chain: List[str]
    risk_factors: Optional[Dict[str, float]]
    recommendations: Optional[List[str]]
    escalation_reason: Optional[str]
    entity_context: Optional[Dict[str, Any]]
    task_context: Optional[Dict[str, Any]]


# Initialize decision engine
decision_engine = DecisionEngine()


def map_location_to_jurisdiction(location: str) -> Jurisdiction:
    """Map location string to Jurisdiction enum"""
    location_map = {
        "US": Jurisdiction.US_FEDERAL,
        "USA": Jurisdiction.US_FEDERAL,
        "UNITED STATES": Jurisdiction.US_FEDERAL,
        "EU": Jurisdiction.EU,
        "EUROPE": Jurisdiction.EU,
        "UK": Jurisdiction.UK,
        "UNITED KINGDOM": Jurisdiction.UK,
        "CANADA": Jurisdiction.CANADA,
        "APAC": Jurisdiction.APAC,
        "ASIA": Jurisdiction.APAC,
    }
    
    location_upper = location.upper().strip()
    return location_map.get(location_upper, Jurisdiction.UNKNOWN)


def generate_compliance_tasks(
    entity: EntityContext,
    jurisdictions: List[Jurisdiction]
) -> List[Dict[str, Any]]:
    """Generate compliance tasks based on entity and jurisdictions"""
    tasks = []
    task_id_counter = 1
    
    # Identify applicable regulations
    regulations = decision_engine.jurisdiction_analyzer.identify_applicable_regulations(
        entity,
        TaskContext(description="Compliance assessment", category=TaskCategory.GENERAL_INQUIRY)
    )
    
    # Common compliance tasks for all entities
    # Modified to include near-term deadlines (0-30 days) with at least one HIGH priority in 7 days
    base_tasks = [
        {
            "name": "Quarterly Compliance Report",
            "description": "Submit quarterly compliance status report to management",
            "category": TaskCategory.POLICY_REVIEW,
            "frequency": "quarterly",
            "deadline_offset": 5,  # HIGH PRIORITY - Due in 5 days
            "affects_personal_data": entity.has_personal_data,
            "potential_impact": "Significant"
        },
        {
            "name": "Data Protection Assessment",
            "description": "Assess data protection measures and privacy controls",
            "category": TaskCategory.DATA_PRIVACY,
            "frequency": "quarterly",
            "deadline_offset": 12,  # MEDIUM PRIORITY - Due in 12 days
            "affects_personal_data": True,
            "potential_impact": "Significant"
        },
        {
            "name": "Security Audit",
            "description": "Conduct security audit of systems and processes",
            "category": TaskCategory.SECURITY_AUDIT,
            "frequency": "quarterly",
            "deadline_offset": 28,  # MEDIUM PRIORITY - Due in 28 days
            "affects_personal_data": entity.has_personal_data,
            "potential_impact": "Significant"
        },
        {
            "name": "Annual Risk Assessment",
            "description": "Comprehensive risk assessment and mitigation planning",
            "category": TaskCategory.RISK_ASSESSMENT,
            "frequency": "annual",
            "deadline_offset": 120,  # LOW PRIORITY - Due in 120 days
            "affects_personal_data": False,
            "potential_impact": "Moderate"
        }
    ]
    
    # Add jurisdiction-specific tasks
    if Jurisdiction.EU in jurisdictions:
        base_tasks.extend([
            {
                "name": "GDPR Data Subject Request Review",
                "description": "Review and respond to pending GDPR data subject access requests",
                "category": TaskCategory.POLICY_REVIEW,
                "frequency": "monthly",
                "deadline_offset": 3,  # HIGH PRIORITY - GDPR requires 30-day response
                "affects_personal_data": True,
                "involves_cross_border": True,
                "potential_impact": "Critical"
            },
            {
                "name": "Data Protection Impact Assessment (DPIA)",
                "description": "Conduct DPIA for new high-risk data processing activities",
                "category": TaskCategory.DATA_PRIVACY,
                "frequency": "as-needed",
                "deadline_offset": 18,  # MEDIUM PRIORITY - Due in 18 days
                "affects_personal_data": True,
                "potential_impact": "Significant"
            }
        ])
    
    if Jurisdiction.US_FEDERAL in jurisdictions:
        if entity.has_personal_data:
            base_tasks.append({
                "name": "Data Breach Response Plan Review",
                "description": "Review and update data breach response procedures",
                "category": TaskCategory.INCIDENT_RESPONSE,
                "frequency": "quarterly",
                "deadline_offset": 22,  # MEDIUM PRIORITY - Due in 22 days
                "affects_personal_data": True,
                "potential_impact": "Critical"
            })
    
    if entity.industry == IndustryCategory.FINANCIAL_SERVICES:
        base_tasks.extend([
            {
                "name": "Quarterly Financial Compliance Report",
                "description": "Prepare and submit Q4 financial compliance reports to regulators",
                "category": TaskCategory.FINANCIAL_REPORTING,
                "frequency": "quarterly",
                "deadline_offset": 6,  # HIGH PRIORITY - Regulatory deadline
                "affects_financial_data": True,
                "potential_impact": "Critical"
            },
            {
                "name": "AML Transaction Monitoring Review",
                "description": "Review flagged transactions and update AML/KYC procedures",
                "category": TaskCategory.POLICY_REVIEW,
                "frequency": "monthly",
                "deadline_offset": 15,  # MEDIUM PRIORITY - Due in 15 days
                "affects_personal_data": True,
                "affects_financial_data": True,
                "potential_impact": "Critical"
            }
        ])
    
    if entity.industry == IndustryCategory.HEALTHCARE:
        base_tasks.append({
            "name": "HIPAA Security Risk Assessment",
            "description": "Complete required HIPAA security risk assessment and remediation plan",
            "category": TaskCategory.SECURITY_AUDIT,
            "frequency": "quarterly",
            "deadline_offset": 25,  # MEDIUM PRIORITY - Due in 25 days
            "affects_personal_data": True,
            "potential_impact": "Critical"
        })
    
    # If entity is regulated, add regulatory filing tasks
    if entity.is_regulated:
        base_tasks.append({
            "name": "Regulatory Filing Submission",
            "description": "Complete and submit Form 10-K regulatory filing to SEC",
            "category": TaskCategory.REGULATORY_FILING,
            "frequency": "quarterly",
            "deadline_offset": 7,  # HIGH PRIORITY - Regulatory deadline approaching
            "affects_financial_data": True,
            "potential_impact": "Critical"
        })
    
    for task_def in base_tasks:
        # Create unique task ID using entity name hash and counter
        entity_hash = abs(hash(entity.name)) % 10000
        task_id = f"TASK-{entity_hash:04d}-{task_id_counter:03d}"
        task_id_counter += 1
        
        # Calculate deadline
        deadline = None
        if task_def.get("deadline_offset"):
            deadline = datetime.utcnow() + timedelta(days=task_def["deadline_offset"])
        
        tasks.append({
            "task_id": task_id,
            "definition": task_def,
            "deadline": deadline
        })
    
    return tasks


@router.post("/entity/analyze", response_model=ComplianceCalendar)
async def analyze_entity(
    request: AnalyzeEntityRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze an entity and return a compliance calendar with autonomy decisions
    
    This endpoint:
    1. Analyzes the entity's characteristics and jurisdictions
    2. Generates a compliance calendar with relevant tasks
    3. For each task, determines if the agent can act autonomously or needs escalation
    4. Returns complete calendar with decisions, confidence scores, and reasoning
    
    Args:
        request: Entity information including name, locations, and characteristics
        db: Database session
        
    Returns:
        ComplianceCalendar with tasks, decisions, and autonomy recommendations
    """
    try:
        # Validate locations
        if not request.locations or len(request.locations) == 0:
            raise HTTPException(
                status_code=422,
                detail="At least one location is required"
            )
        
        # Map locations to jurisdictions
        jurisdictions = [map_location_to_jurisdiction(loc) for loc in request.locations]
        
        # Handle multi-jurisdictional cases
        if len(jurisdictions) > 1:
            jurisdictions.append(Jurisdiction.MULTI_JURISDICTIONAL)
        
        # Create entity context
        entity = EntityContext(
            name=request.entity_name,
            entity_type=EntityType[request.entity_type] if request.entity_type in EntityType.__members__ else EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory[request.industry] if request.industry in IndustryCategory.__members__ else IndustryCategory.TECHNOLOGY,
            jurisdictions=jurisdictions,
            employee_count=request.employee_count,
            annual_revenue=request.annual_revenue,
            has_personal_data=request.has_personal_data,
            is_regulated=request.is_regulated,
            previous_violations=request.previous_violations
        )
        
        # Generate compliance tasks
        compliance_tasks = generate_compliance_tasks(entity, jurisdictions)
        
        # Analyze each task and get decision
        analyzed_tasks = []
        decisions_summary = {
            "autonomous": 0,
            "review_required": 0,
            "escalate": 0
        }
        
        for task_info in compliance_tasks:
            task_def = task_info["definition"]
            
            # Create task context
            task = TaskContext(
                description=task_def["description"],
                category=task_def["category"],
                affects_personal_data=task_def.get("affects_personal_data", False),
                affects_financial_data=task_def.get("affects_financial_data", False),
                involves_cross_border=task_def.get("involves_cross_border", False),
                regulatory_deadline=task_info.get("deadline"),
                potential_impact=task_def.get("potential_impact", "Moderate")
            )
            
            # Run decision analysis
            analysis = decision_engine.analyze_and_decide(entity, task)
            
            # Log to audit trail
            audit_entry = AuditService.log_decision_analysis(
                db=db,
                analysis=analysis,
                agent_type="decision_engine",
                metadata={
                    "api_endpoint": "/entity/analyze",
                    "task_id": task_info["task_id"],
                    "frequency": task_def["frequency"]
                }
            )
            
            # Create reasoning summary (first 3 key points)
            key_reasoning = []
            for reason in analysis.reasoning:
                if any(keyword in reason for keyword in ["RISK", "DECISION", "risk", "decision", "🎯", "🤔", "⚠️", "🚨"]):
                    key_reasoning.append(reason.strip())
                    if len(key_reasoning) >= 3:
                        break
            
            reasoning_summary = " | ".join(key_reasoning[:3]) if key_reasoning else "Standard compliance analysis"
            
            # Count decisions
            decisions_summary[analysis.decision.value.lower().replace("_", "")] = \
                decisions_summary.get(analysis.decision.value.lower().replace("_", ""), 0) + 1
            
            analyzed_tasks.append(ComplianceTask(
                task_id=task_info["task_id"],
                task_name=task_def["name"],
                description=task_def["description"],
                category=task_def["category"].value,
                deadline=task_info["deadline"].isoformat() if task_info["deadline"] else None,
                frequency=task_def["frequency"],
                decision=analysis.decision.value,
                confidence=analysis.confidence,
                risk_level=analysis.risk_level.value,
                reasoning_summary=reasoning_summary,
                audit_id=audit_entry.id
            ))
        
        # Identify applicable regulations
        sample_task = TaskContext(
            description="Compliance assessment",
            category=TaskCategory.GENERAL_INQUIRY
        )
        applicable_regulations = decision_engine.jurisdiction_analyzer.identify_applicable_regulations(
            entity, sample_task
        )
        
        # Create summary with timestamps for data consistency tracking
        from datetime import datetime
        summary = {
            "total_tasks": len(analyzed_tasks),
            "decisions": decisions_summary,
            "average_confidence": sum(t.confidence for t in analyzed_tasks) / len(analyzed_tasks) if analyzed_tasks else 0,
            "high_risk_tasks": sum(1 for t in analyzed_tasks if t.risk_level == "HIGH"),
            "medium_risk_tasks": sum(1 for t in analyzed_tasks if t.risk_level == "MEDIUM"),
            "low_risk_tasks": sum(1 for t in analyzed_tasks if t.risk_level == "LOW"),
            "last_updated": datetime.utcnow().isoformat(),
            "calculation_timestamp": datetime.utcnow().isoformat(),
            "autonomous_percentage": (decisions_summary["autonomous"] / len(analyzed_tasks) * 100) if analyzed_tasks else 0
        }
        
        return ComplianceCalendar(
            entity_name=request.entity_name,
            jurisdictions=request.locations,
            applicable_regulations=applicable_regulations,
            tasks=analyzed_tasks,
            summary=summary
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity analysis failed: {str(e)}")


@router.get("/audit_log/{task_id}", response_model=AuditLogResponse)
async def get_audit_log(
    task_id: str = Path(..., description="Task ID from the compliance calendar"),
    db: Session = Depends(get_db)
):
    """
    Retrieve the complete audit log and reasoning for a specific task
    
    This endpoint returns the full audit trail entry for a task, including:
    - Complete reasoning chain (step-by-step decision logic)
    - Risk factors breakdown
    - Confidence scores
    - Recommendations
    - Full entity and task context
    
    Args:
        task_id: Task ID (e.g., "TASK-0001")
        db: Database session
        
    Returns:
        Complete audit log with reasoning chain
    """
    try:
        # Query audit trail by task_id in metadata
        from backend.db.models import AuditTrail
        from sqlalchemy import func
        
        # Use SQLite's JSON extraction to find matching task_id
        # This works with SQLite's json_extract function
        audit_entry = db.query(AuditTrail).filter(
            func.json_extract(AuditTrail.meta_data, '$.task_id') == task_id
        ).order_by(AuditTrail.timestamp.desc()).first()
        
        if not audit_entry:
            raise HTTPException(
                status_code=404,
                detail=f"Audit log not found for task_id: {task_id}"
            )
        
        return AuditLogResponse(
            task_id=task_id,
            audit_id=audit_entry.id,
            timestamp=audit_entry.timestamp.isoformat(),
            entity_name=audit_entry.entity_name,
            task_description=audit_entry.task_description,
            task_category=audit_entry.task_category,
            decision_outcome=audit_entry.decision_outcome,
            confidence_score=audit_entry.confidence_score,
            risk_level=audit_entry.risk_level,
            risk_score=audit_entry.risk_score,
            reasoning_chain=audit_entry.reasoning_chain,
            risk_factors=audit_entry.risk_factors,
            recommendations=audit_entry.recommendations,
            escalation_reason=audit_entry.escalation_reason,
            entity_context=audit_entry.entity_context,
            task_context=audit_entry.task_context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit log: {str(e)}")

