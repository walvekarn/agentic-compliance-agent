"""Tests for the decision engine"""

import pytest
from backend.agent.decision_engine import DecisionEngine
from backend.agent.risk_models import (
    EntityContext,
    TaskContext,
    EntityType,
    IndustryCategory,
    Jurisdiction,
    TaskCategory,
    RiskLevel,
    ActionDecision
)


@pytest.fixture
def decision_engine():
    """Create decision engine instance"""
    return DecisionEngine()


@pytest.fixture
def low_risk_entity():
    """Create a low-risk entity context"""
    return EntityContext(
        name="Small Tech Startup",
        entity_type=EntityType.STARTUP,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_STATE],
        employee_count=25,
        annual_revenue=2_000_000,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=0
    )


@pytest.fixture
def high_risk_entity():
    """Create a high-risk entity context"""
    return EntityContext(
        name="Major Financial Institution",
        entity_type=EntityType.FINANCIAL_INSTITUTION,
        industry=IndustryCategory.FINANCIAL_SERVICES,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
        employee_count=10000,
        annual_revenue=5_000_000_000,
        has_personal_data=True,
        is_regulated=True,
        previous_violations=1
    )


@pytest.fixture
def low_risk_task():
    """Create a low-risk task context"""
    return TaskContext(
        description="General inquiry about GDPR principles",
        category=TaskCategory.GENERAL_INQUIRY,
        affects_personal_data=False,
        affects_financial_data=False,
        involves_cross_border=False
    )


@pytest.fixture
def high_risk_task():
    """Create a high-risk task context"""
    return TaskContext(
        description="Handle data breach incident involving customer financial data",
        category=TaskCategory.INCIDENT_RESPONSE,
        affects_personal_data=True,
        affects_financial_data=True,
        involves_cross_border=True,
        potential_impact="Critical - affects 100,000 customers",
        stakeholder_count=100000
    )


def test_low_risk_autonomous_decision(decision_engine, low_risk_entity, low_risk_task):
    """Test that low risk scenarios can result in autonomous action"""
    analysis = decision_engine.analyze_and_decide(low_risk_entity, low_risk_task)
    
    assert analysis.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    assert analysis.decision in [ActionDecision.AUTONOMOUS, ActionDecision.REVIEW_REQUIRED]
    assert analysis.confidence > 0.6
    assert len(analysis.reasoning) > 5
    assert len(analysis.recommendations) > 0


def test_high_risk_escalation(decision_engine, high_risk_entity, high_risk_task):
    """Test that high risk scenarios trigger escalation"""
    analysis = decision_engine.analyze_and_decide(high_risk_entity, high_risk_task)
    
    assert analysis.risk_level == RiskLevel.HIGH
    assert analysis.decision == ActionDecision.ESCALATE
    assert analysis.confidence > 0.8
    assert analysis.escalation_reason is not None
    assert "incident response" in analysis.escalation_reason.lower() or "high" in analysis.escalation_reason.lower()


def test_medium_risk_review_required(decision_engine):
    """Test medium risk scenarios require review"""
    entity = EntityContext(
        name="Medium Corp",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.RETAIL,
        jurisdictions=[Jurisdiction.US_FEDERAL],
        employee_count=500,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=0
    )
    
    task = TaskContext(
        description="Review data privacy policy for CCPA compliance",
        category=TaskCategory.POLICY_REVIEW,
        affects_personal_data=True,
        affects_financial_data=False,
        involves_cross_border=False
    )
    
    analysis = decision_engine.analyze_and_decide(entity, task)
    
    # Should be medium risk requiring review
    assert analysis.risk_level in [RiskLevel.MEDIUM, RiskLevel.LOW]
    if analysis.risk_level == RiskLevel.MEDIUM:
        assert analysis.decision == ActionDecision.REVIEW_REQUIRED


def test_multi_jurisdictional_increases_risk(decision_engine, low_risk_task):
    """Test that multiple jurisdictions increase risk"""
    multi_jurisdiction_entity = EntityContext(
        name="Global Company",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU, Jurisdiction.APAC],
        employee_count=1000,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=0
    )
    
    analysis = decision_engine.analyze_and_decide(multi_jurisdiction_entity, low_risk_task)
    
    # Multiple jurisdictions should be mentioned in reasoning
    reasoning_text = " ".join(analysis.reasoning).lower()
    assert "jurisdiction" in reasoning_text
    assert analysis.risk_factors.jurisdiction_risk > 0.6


def test_previous_violations_affect_decision(decision_engine, low_risk_task):
    """Test that previous violations impact decision"""
    entity_with_violations = EntityContext(
        name="Company With Violations",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_STATE],
        employee_count=200,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=3
    )
    
    analysis = decision_engine.analyze_and_decide(entity_with_violations, low_risk_task)
    
    # Previous violations should be mentioned
    reasoning_text = " ".join(analysis.reasoning).lower()
    assert "violation" in reasoning_text
    
    # Should affect decision - less likely to be autonomous
    if analysis.risk_level == RiskLevel.LOW:
        # Even with low risk, violations may trigger review
        assert analysis.decision in [ActionDecision.REVIEW_REQUIRED, ActionDecision.AUTONOMOUS]


def test_incident_response_always_escalates(decision_engine, low_risk_entity):
    """Test that incident response tasks always escalate"""
    incident_task = TaskContext(
        description="Minor security incident - unauthorized access attempt",
        category=TaskCategory.INCIDENT_RESPONSE,
        affects_personal_data=False,
        affects_financial_data=False,
        involves_cross_border=False,
        potential_impact="Minor"
    )
    
    analysis = decision_engine.analyze_and_decide(low_risk_entity, incident_task)
    
    # Incident response should always escalate
    assert analysis.decision == ActionDecision.ESCALATE


def test_financial_institution_high_risk(decision_engine, low_risk_task):
    """Test that financial institutions are treated as high risk"""
    financial_entity = EntityContext(
        name="Bank",
        entity_type=EntityType.FINANCIAL_INSTITUTION,
        industry=IndustryCategory.FINANCIAL_SERVICES,
        jurisdictions=[Jurisdiction.US_FEDERAL],
        employee_count=5000,
        has_personal_data=True,
        is_regulated=True,
        previous_violations=0
    )
    
    analysis = decision_engine.analyze_and_decide(financial_entity, low_risk_task)
    
    # Financial institution should have elevated entity risk
    assert analysis.risk_factors.entity_risk > 0.7
    reasoning_text = " ".join(analysis.reasoning).lower()
    assert "financial" in reasoning_text or "regulated" in reasoning_text


def test_cross_border_data_transfer(decision_engine):
    """Test cross-border data transfer risks"""
    entity = EntityContext(
        name="EU Company",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.EU],
        employee_count=100,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=0
    )
    
    cross_border_task = TaskContext(
        description="Transfer customer data to US servers",
        category=TaskCategory.DATA_PRIVACY,
        affects_personal_data=True,
        affects_financial_data=False,
        involves_cross_border=True
    )
    
    analysis = decision_engine.analyze_and_decide(entity, cross_border_task)
    
    # Cross-border should increase risk
    reasoning_text = " ".join(analysis.reasoning).lower()
    assert "cross-border" in reasoning_text or "transfer" in reasoning_text
    assert analysis.risk_factors.jurisdiction_risk > 0.6


def test_risk_factors_calculation(decision_engine, low_risk_entity, low_risk_task):
    """Test that risk factors are properly calculated"""
    analysis = decision_engine.analyze_and_decide(low_risk_entity, low_risk_task)
    
    # All risk factors should be between 0 and 1
    assert 0 <= analysis.risk_factors.jurisdiction_risk <= 1
    assert 0 <= analysis.risk_factors.entity_risk <= 1
    assert 0 <= analysis.risk_factors.task_risk <= 1
    assert 0 <= analysis.risk_factors.data_sensitivity_risk <= 1
    assert 0 <= analysis.risk_factors.regulatory_risk <= 1
    assert 0 <= analysis.risk_factors.impact_risk <= 1
    
    # Overall score should also be in valid range
    assert 0 <= analysis.risk_factors.overall_score <= 1


def test_recommendations_provided(decision_engine, high_risk_entity, high_risk_task):
    """Test that recommendations are always provided"""
    analysis = decision_engine.analyze_and_decide(high_risk_entity, high_risk_task)
    
    assert len(analysis.recommendations) > 0
    
    # Escalation scenarios should have appropriate recommendations
    if analysis.decision == ActionDecision.ESCALATE:
        recommendations_text = " ".join(analysis.recommendations).lower()
        assert "escalate" in recommendations_text or "specialist" in recommendations_text


def test_healthcare_entity_risk(decision_engine):
    """Test healthcare entities have appropriate risk assessment"""
    healthcare_entity = EntityContext(
        name="Hospital",
        entity_type=EntityType.HEALTHCARE,
        industry=IndustryCategory.HEALTHCARE,
        jurisdictions=[Jurisdiction.US_FEDERAL],
        employee_count=3000,
        has_personal_data=True,
        is_regulated=True,
        previous_violations=0
    )
    
    healthcare_task = TaskContext(
        description="Update patient data handling procedures",
        category=TaskCategory.DATA_PRIVACY,
        affects_personal_data=True,
        affects_financial_data=False,
        involves_cross_border=False
    )
    
    analysis = decision_engine.analyze_and_decide(healthcare_entity, healthcare_task)
    
    # Healthcare should have high entity risk
    assert analysis.risk_factors.entity_risk > 0.7
    reasoning_text = " ".join(analysis.reasoning).lower()
    assert "healthcare" in reasoning_text or "hipaa" in reasoning_text or "health" in reasoning_text

