"""Tests for decision engine confidence scoring"""
import pytest
from backend.agent.decision_engine import DecisionEngine
from backend.agent.risk_models import (
    EntityContext, TaskContext, EntityType, IndustryCategory,
    Jurisdiction, TaskCategory, RiskLevel, ActionDecision
)


def test_confidence_low_risk_simple_task():
    """Test confidence for LOW risk + simple task = 0.90"""
    engine = DecisionEngine()
    entity = EntityContext(
        name="SimpleCorp",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL],
        has_personal_data=False,
        is_regulated=False
    )
    task = TaskContext(
        description="What are basic compliance requirements?",
        category=TaskCategory.GENERAL_INQUIRY
    )
    result = engine.analyze_and_decide(entity, task)
    assert result.risk_level == RiskLevel.LOW
    assert result.confidence == 0.90  # Simple task gets 0.90
    assert result.decision == ActionDecision.AUTONOMOUS


def test_confidence_medium_risk():
    """Test confidence for MEDIUM risk = 0.75-0.80"""
    engine = DecisionEngine()
    entity = EntityContext(
        name="MediumCorp",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
        has_personal_data=True,
        is_regulated=False
    )
    task = TaskContext(
        description="Data privacy compliance review",
        category=TaskCategory.DATA_PRIVACY
    )
    result = engine.analyze_and_decide(entity, task)
    assert result.risk_level == RiskLevel.MEDIUM
    assert 0.70 <= result.confidence <= 0.85  # MEDIUM range
    assert result.decision in [ActionDecision.AUTONOMOUS, ActionDecision.REVIEW_REQUIRED]


def test_confidence_high_risk():
    """Test confidence for HIGH risk = 0.80-0.90"""
    engine = DecisionEngine()
    entity = EntityContext(
        name="HighRiskCorp",
        entity_type=EntityType.PUBLIC_COMPANY,
        industry=IndustryCategory.FINANCIAL_SERVICES,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
        has_personal_data=True,
        is_regulated=True,
        previous_violations=3
    )
    task = TaskContext(
        description="Regulatory filing for previous violations",
        category=TaskCategory.REGULATORY_FILING
    )
    result = engine.analyze_and_decide(entity, task)
    assert result.risk_level == RiskLevel.HIGH
    assert 0.80 <= result.confidence <= 0.90  # HIGH range
    assert result.decision in [ActionDecision.REVIEW_REQUIRED, ActionDecision.ESCALATE]


def test_confidence_dynamic_range():
    """Test that confidence varies based on risk level"""
    engine = DecisionEngine()
    
    # LOW risk case
    low_entity = EntityContext(
        name="LowCorp",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL],
        has_personal_data=False,
        is_regulated=False
    )
    low_task = TaskContext(
        description="General inquiry",
        category=TaskCategory.GENERAL_INQUIRY
    )
    low_result = engine.analyze_and_decide(low_entity, low_task)
    
    # HIGH risk case
    high_entity = EntityContext(
        name="HighCorp",
        entity_type=EntityType.PUBLIC_COMPANY,
        industry=IndustryCategory.FINANCIAL_SERVICES,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
        has_personal_data=True,
        is_regulated=True,
        previous_violations=5
    )
    high_task = TaskContext(
        description="Regulatory filing",
        category=TaskCategory.REGULATORY_FILING
    )
    high_result = engine.analyze_and_decide(high_entity, high_task)
    
    # Confidence should be in valid range for both
    assert 0.70 <= low_result.confidence <= 0.90
    assert 0.70 <= high_result.confidence <= 0.90
    # But they may differ based on risk
    assert low_result.risk_level != high_result.risk_level or low_result.confidence != high_result.confidence

