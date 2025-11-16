"""Sample test data for pytest tests"""

from src.agent.risk_models import (
    EntityContext,
    TaskContext,
    EntityType,
    IndustryCategory,
    Jurisdiction,
    TaskCategory
)
from datetime import datetime, timedelta


# Sample Entities
SAMPLE_STARTUP = EntityContext(
    name="TechStartup Inc",
    entity_type=EntityType.STARTUP,
    industry=IndustryCategory.TECHNOLOGY,
    jurisdictions=[Jurisdiction.US_FEDERAL],
    employee_count=25,
    annual_revenue=1_000_000.0,
    has_personal_data=False,
    is_regulated=False,
    previous_violations=0
)

SAMPLE_PRIVATE_COMPANY = EntityContext(
    name="GlobalTech Solutions",
    entity_type=EntityType.PRIVATE_COMPANY,
    industry=IndustryCategory.TECHNOLOGY,
    jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
    employee_count=500,
    annual_revenue=50_000_000.0,
    has_personal_data=True,
    is_regulated=False,
    previous_violations=0
)

SAMPLE_PUBLIC_COMPANY = EntityContext(
    name="MegaCorp International",
    entity_type=EntityType.PUBLIC_COMPANY,
    industry=IndustryCategory.TECHNOLOGY,
    jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU, Jurisdiction.UK],
    employee_count=5000,
    annual_revenue=500_000_000.0,
    has_personal_data=True,
    is_regulated=True,
    previous_violations=0
)

SAMPLE_FINANCIAL_INSTITUTION = EntityContext(
    name="SecureBank Corp",
    entity_type=EntityType.FINANCIAL_INSTITUTION,
    industry=IndustryCategory.FINANCIAL_SERVICES,
    jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
    employee_count=2500,
    annual_revenue=200_000_000.0,
    has_personal_data=True,
    is_regulated=True,
    previous_violations=0
)

SAMPLE_HEALTHCARE_ORG = EntityContext(
    name="HealthCare Plus",
    entity_type=EntityType.HEALTHCARE,
    industry=IndustryCategory.HEALTHCARE,
    jurisdictions=[Jurisdiction.US_FEDERAL],
    employee_count=800,
    annual_revenue=75_000_000.0,
    has_personal_data=True,
    is_regulated=True,
    previous_violations=0
)

SAMPLE_COMPANY_WITH_VIOLATIONS = EntityContext(
    name="Troubled Corp",
    entity_type=EntityType.PRIVATE_COMPANY,
    industry=IndustryCategory.TECHNOLOGY,
    jurisdictions=[Jurisdiction.US_FEDERAL],
    employee_count=200,
    annual_revenue=10_000_000.0,
    has_personal_data=True,
    is_regulated=False,
    previous_violations=3
)

# Sample Tasks
SAMPLE_GENERAL_INQUIRY = TaskContext(
    description="What are the basic requirements for GDPR compliance?",
    category=TaskCategory.GENERAL_INQUIRY,
    affects_personal_data=False,
    affects_financial_data=False,
    involves_cross_border=False
)

SAMPLE_POLICY_REVIEW = TaskContext(
    description="Review and update data privacy policy",
    category=TaskCategory.POLICY_REVIEW,
    affects_personal_data=True,
    affects_financial_data=False,
    involves_cross_border=False,
    potential_impact="Moderate"
)

SAMPLE_SECURITY_AUDIT = TaskContext(
    description="Conduct comprehensive security audit of customer database",
    category=TaskCategory.SECURITY_AUDIT,
    affects_personal_data=True,
    affects_financial_data=False,
    involves_cross_border=False,
    potential_impact="Significant",
    stakeholder_count=10000
)

SAMPLE_DATA_PRIVACY_TASK = TaskContext(
    description="Implement GDPR data subject access request process",
    category=TaskCategory.DATA_PRIVACY,
    affects_personal_data=True,
    affects_financial_data=False,
    involves_cross_border=True,
    potential_impact="Significant"
)

SAMPLE_FINANCIAL_REPORTING = TaskContext(
    description="Prepare quarterly financial compliance report",
    category=TaskCategory.FINANCIAL_REPORTING,
    affects_personal_data=False,
    affects_financial_data=True,
    involves_cross_border=False,
    regulatory_deadline=datetime.utcnow() + timedelta(days=30),
    potential_impact="Critical"
)

SAMPLE_REGULATORY_FILING = TaskContext(
    description="Submit annual regulatory compliance filing",
    category=TaskCategory.REGULATORY_FILING,
    affects_personal_data=True,
    affects_financial_data=True,
    involves_cross_border=True,
    regulatory_deadline=datetime.utcnow() + timedelta(days=45),
    potential_impact="Critical",
    stakeholder_count=50000
)

SAMPLE_INCIDENT_RESPONSE = TaskContext(
    description="Data breach affecting 100,000 customers",
    category=TaskCategory.INCIDENT_RESPONSE,
    affects_personal_data=True,
    affects_financial_data=True,
    involves_cross_border=True,
    potential_impact="Critical",
    stakeholder_count=100000
)

SAMPLE_RISK_ASSESSMENT = TaskContext(
    description="Annual enterprise risk assessment",
    category=TaskCategory.RISK_ASSESSMENT,
    affects_personal_data=False,
    affects_financial_data=False,
    involves_cross_border=False,
    potential_impact="Moderate"
)

SAMPLE_CONTRACT_REVIEW = TaskContext(
    description="Review vendor data processing agreement",
    category=TaskCategory.CONTRACT_REVIEW,
    affects_personal_data=True,
    affects_financial_data=False,
    involves_cross_border=True,
    potential_impact="Moderate"
)

# Test Scenarios (entity + task combinations)
SCENARIOS = {
    "low_risk_autonomous": {
        "entity": SAMPLE_STARTUP,
        "task": SAMPLE_GENERAL_INQUIRY,
        "expected_risk_level": "LOW",
        "expected_decision": ["AUTONOMOUS", "REVIEW_REQUIRED"]  # Either is acceptable
    },
    "medium_risk_review": {
        "entity": SAMPLE_PRIVATE_COMPANY,
        "task": SAMPLE_POLICY_REVIEW,
        "expected_risk_level": ["LOW", "MEDIUM"],
        "expected_decision": ["REVIEW_REQUIRED", "AUTONOMOUS"]
    },
    "high_risk_escalate": {
        "entity": SAMPLE_FINANCIAL_INSTITUTION,
        "task": SAMPLE_INCIDENT_RESPONSE,
        "expected_risk_level": "HIGH",
        "expected_decision": ["ESCALATE"]
    },
    "financial_institution_audit": {
        "entity": SAMPLE_FINANCIAL_INSTITUTION,
        "task": SAMPLE_SECURITY_AUDIT,
        "expected_risk_level": ["MEDIUM", "HIGH"],
        "expected_decision": ["REVIEW_REQUIRED", "ESCALATE"]
    },
    "healthcare_privacy": {
        "entity": SAMPLE_HEALTHCARE_ORG,
        "task": SAMPLE_DATA_PRIVACY_TASK,
        "expected_risk_level": ["MEDIUM", "HIGH"],
        "expected_decision": ["REVIEW_REQUIRED", "ESCALATE"]
    },
    "violations_history": {
        "entity": SAMPLE_COMPANY_WITH_VIOLATIONS,
        "task": SAMPLE_POLICY_REVIEW,
        "expected_risk_level": ["MEDIUM"],
        "expected_decision": ["REVIEW_REQUIRED", "ESCALATE"]  # Should require review due to violations
    },
    "regulatory_filing": {
        "entity": SAMPLE_PUBLIC_COMPANY,
        "task": SAMPLE_REGULATORY_FILING,
        "expected_risk_level": ["HIGH"],
        "expected_decision": ["ESCALATE", "REVIEW_REQUIRED"]
    }
}

# API Request Samples
SAMPLE_API_REQUESTS = {
    "minimal_request": {
        "entity_name": "TestCorp",
        "locations": ["US"]
    },
    "full_request": {
        "entity_name": "GlobalTech Solutions",
        "locations": ["US", "EU", "UK"],
        "entity_type": "PRIVATE_COMPANY",
        "industry": "TECHNOLOGY",
        "employee_count": 500,
        "annual_revenue": 50000000.0,
        "has_personal_data": True,
        "is_regulated": False,
        "previous_violations": 0
    },
    "financial_institution": {
        "entity_name": "SecureBank Corp",
        "locations": ["US"],
        "entity_type": "FINANCIAL_INSTITUTION",
        "industry": "FINANCIAL_SERVICES",
        "employee_count": 2500,
        "has_personal_data": True,
        "is_regulated": True
    },
    "healthcare_org": {
        "entity_name": "HealthCare Plus",
        "locations": ["US"],
        "entity_type": "HEALTHCARE",
        "industry": "HEALTHCARE",
        "employee_count": 800,
        "has_personal_data": True
    },
    "startup": {
        "entity_name": "StartupCo",
        "locations": ["US"],
        "entity_type": "STARTUP",
        "industry": "TECHNOLOGY",
        "employee_count": 25,
        "has_personal_data": False,
        "previous_violations": 0
    },
    "eu_entity": {
        "entity_name": "EuroTech",
        "locations": ["EU"],
        "entity_type": "PRIVATE_COMPANY",
        "industry": "TECHNOLOGY",
        "has_personal_data": True
    },
    "multi_jurisdiction": {
        "entity_name": "GlobalCorp",
        "locations": ["US", "EU", "UK", "CANADA"],
        "entity_type": "PUBLIC_COMPANY",
        "industry": "TECHNOLOGY",
        "employee_count": 10000,
        "has_personal_data": True,
        "is_regulated": True
    }
}

# Expected Response Structures
EXPECTED_RESPONSE_KEYS = {
    "analyze_entity": [
        "entity_name",
        "jurisdictions",
        "applicable_regulations",
        "tasks",
        "summary"
    ],
    "task_object": [
        "task_id",
        "task_name",
        "description",
        "category",
        "deadline",
        "frequency",
        "decision",
        "confidence",
        "risk_level",
        "reasoning_summary",
        "audit_id"
    ],
    "summary_object": [
        "total_tasks",
        "decisions",
        "average_confidence",
        "high_risk_tasks",
        "medium_risk_tasks",
        "low_risk_tasks",
        "autonomous_percentage"
    ],
    "audit_log": [
        "task_id",
        "audit_id",
        "timestamp",
        "entity_name",
        "task_description",
        "task_category",
        "decision_outcome",
        "confidence_score",
        "risk_level",
        "risk_score",
        "reasoning_chain",
        "risk_factors",
        "recommendations",
        "escalation_reason",
        "entity_context",
        "task_context"
    ],
    "risk_factors": [
        "jurisdiction_risk",
        "entity_risk",
        "task_risk",
        "data_sensitivity_risk",
        "regulatory_risk",
        "impact_risk",
        "overall_score"
    ]
}

# Test Constants
VALID_DECISION_OUTCOMES = ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
VALID_RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]
VALID_TASK_CATEGORIES = [
    "DATA_PRIVACY",
    "FINANCIAL_REPORTING",
    "SECURITY_AUDIT",
    "POLICY_REVIEW",
    "REGULATORY_FILING",
    "CONTRACT_REVIEW",
    "INCIDENT_RESPONSE",
    "RISK_ASSESSMENT",
    "GENERAL_INQUIRY"
]
VALID_ENTITY_TYPES = [
    "PUBLIC_COMPANY",
    "PRIVATE_COMPANY",
    "STARTUP",
    "NONPROFIT",
    "GOVERNMENT",
    "HEALTHCARE",
    "FINANCIAL_INSTITUTION"
]
VALID_INDUSTRIES = [
    "HEALTHCARE",
    "FINANCIAL_SERVICES",
    "TECHNOLOGY",
    "RETAIL",
    "MANUFACTURING",
    "EDUCATION",
    "GOVERNMENT",
    "OTHER"
]
VALID_LOCATIONS = ["US", "EU", "UK", "CANADA", "APAC"]

# Helper function to get sample data
def get_entity(entity_type: str) -> EntityContext:
    """Get a sample entity by type"""
    entities = {
        "startup": SAMPLE_STARTUP,
        "private_company": SAMPLE_PRIVATE_COMPANY,
        "public_company": SAMPLE_PUBLIC_COMPANY,
        "financial_institution": SAMPLE_FINANCIAL_INSTITUTION,
        "healthcare": SAMPLE_HEALTHCARE_ORG,
        "with_violations": SAMPLE_COMPANY_WITH_VIOLATIONS
    }
    return entities.get(entity_type)

def get_task(task_type: str) -> TaskContext:
    """Get a sample task by type"""
    tasks = {
        "general_inquiry": SAMPLE_GENERAL_INQUIRY,
        "policy_review": SAMPLE_POLICY_REVIEW,
        "security_audit": SAMPLE_SECURITY_AUDIT,
        "data_privacy": SAMPLE_DATA_PRIVACY_TASK,
        "financial_reporting": SAMPLE_FINANCIAL_REPORTING,
        "regulatory_filing": SAMPLE_REGULATORY_FILING,
        "incident_response": SAMPLE_INCIDENT_RESPONSE,
        "risk_assessment": SAMPLE_RISK_ASSESSMENT,
        "contract_review": SAMPLE_CONTRACT_REVIEW
    }
    return tasks.get(task_type)

def get_scenario(scenario_name: str) -> dict:
    """Get a test scenario by name"""
    return SCENARIOS.get(scenario_name)

def get_api_request(request_type: str) -> dict:
    """Get a sample API request by type"""
    return SAMPLE_API_REQUESTS.get(request_type)

