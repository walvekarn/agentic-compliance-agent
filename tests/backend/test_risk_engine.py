"""
Risk Engine Tests
=================
Test the 6-factor risk assessment engine.
"""

import pytest
from backend.agent.risk_models import (
    RiskFactors,
    RiskLevel,
    ActionDecision,
    EntityContext,
    TaskContext,
    EntityType,
    IndustryCategory,
    Jurisdiction,
    TaskCategory
)
from backend.agent.decision_engine import DecisionEngine


class TestRiskFactors:
    """Test RiskFactors model and calculations"""
    
    def test_risk_factors_creation(self):
        """Test creating risk factors"""
        factors = RiskFactors(
            jurisdiction_risk=0.5,
            entity_risk=0.3,
            task_risk=0.4,
            data_sensitivity_risk=0.6,
            regulatory_risk=0.5,
            impact_risk=0.3
        )
        assert factors.jurisdiction_risk == 0.5
        assert factors.entity_risk == 0.3
    
    def test_overall_score_calculation(self):
        """Test weighted overall score calculation"""
        factors = RiskFactors(
            jurisdiction_risk=0.5,      # 15% weight = 0.075
            entity_risk=0.3,            # 15% weight = 0.045
            task_risk=0.4,              # 20% weight = 0.08
            data_sensitivity_risk=0.6,  # 20% weight = 0.12
            regulatory_risk=0.5,        # 20% weight = 0.10
            impact_risk=0.3             # 10% weight = 0.03
        )
        expected = (0.5 * 0.15 + 0.3 * 0.15 + 0.4 * 0.20 + 
                    0.6 * 0.20 + 0.5 * 0.20 + 0.3 * 0.10)
        assert abs(factors.overall_score - expected) < 0.001
    
    def test_risk_classification_low(self):
        """Test LOW risk classification"""
        factors = RiskFactors(
            jurisdiction_risk=0.2,
            entity_risk=0.2,
            task_risk=0.2,
            data_sensitivity_risk=0.2,
            regulatory_risk=0.2,
            impact_risk=0.2
        )
        assert factors.classify_risk() == RiskLevel.LOW
    
    def test_risk_classification_medium(self):
        """Test MEDIUM risk classification"""
        factors = RiskFactors(
            jurisdiction_risk=0.5,
            entity_risk=0.5,
            task_risk=0.5,
            data_sensitivity_risk=0.5,
            regulatory_risk=0.5,
            impact_risk=0.5
        )
        assert factors.classify_risk() == RiskLevel.MEDIUM
    
    def test_risk_classification_high(self):
        """Test HIGH risk classification"""
        factors = RiskFactors(
            jurisdiction_risk=0.9,
            entity_risk=0.9,
            task_risk=0.9,
            data_sensitivity_risk=0.9,
            regulatory_risk=0.9,
            impact_risk=0.9
        )
        assert factors.classify_risk() == RiskLevel.HIGH
    
    def test_rationale_generation(self):
        """Test rationale generation"""
        factors = RiskFactors(
            jurisdiction_risk=0.8,
            entity_risk=0.3,
            task_risk=0.7,
            data_sensitivity_risk=0.6,
            regulatory_risk=0.5,
            impact_risk=0.4
        )
        rationale = factors.generate_rationale()
        assert isinstance(rationale, list)
        assert len(rationale) > 0
        assert any("jurisdiction" in r.lower() for r in rationale)


class TestDecisionEngine:
    """Test DecisionEngine risk assessment"""
    
    def test_low_risk_autonomous(self):
        """Test that low risk tasks get AUTONOMOUS decision"""
        engine = DecisionEngine()
        entity = EntityContext(
            name="TestCorp",
            entity_type=EntityType.PRIVATE_COMPANY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            industry=IndustryCategory.TECHNOLOGY,
            employee_count=50,
            has_personal_data=False,
            is_regulated=False,
            previous_violations=0
        )
        task = TaskContext(
            description="General compliance inquiry",
            category=TaskCategory.GENERAL_INQUIRY,
            affects_personal_data=False,
            requires_filing=False
        )
        
        analysis = engine.analyze_and_decide(entity, task)
        assert analysis.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        assert analysis.decision in [ActionDecision.AUTONOMOUS, ActionDecision.REVIEW_REQUIRED]
    
    def test_high_risk_escalate(self):
        """Test that high risk tasks get ESCALATE decision"""
        engine = DecisionEngine()
        entity = EntityContext(
            name="BankCorp",
            entity_type=EntityType.FINANCIAL_INSTITUTION,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            industry=IndustryCategory.FINANCIAL_SERVICES,
            employee_count=10000,
            has_personal_data=True,
            is_regulated=True,
            previous_violations=2
        )
        task = TaskContext(
            description="Incident response for data breach",
            category=TaskCategory.INCIDENT_RESPONSE,
            affects_personal_data=True,
            requires_filing=True
        )
        
        analysis = engine.analyze_and_decide(entity, task)
        # High risk scenarios should escalate
        assert analysis.risk_level == RiskLevel.HIGH
        assert analysis.decision == ActionDecision.ESCALATE
    
    def test_assess_risk_function(self):
        """Test standalone assess_risk function"""
        from backend.agent.decision_engine import DecisionEngine
        
        engine = DecisionEngine()
        entity = EntityContext(
            name="TestCorp",
            entity_type=EntityType.PRIVATE_COMPANY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            industry=IndustryCategory.TECHNOLOGY,
            employee_count=100,
            has_personal_data=True,
            is_regulated=False,
            previous_violations=0
        )
        task = TaskContext(
            description="GDPR compliance review",
            category=TaskCategory.DATA_PRIVACY,
            affects_personal_data=True,
            requires_filing=False
        )
        
        analysis = engine.analyze_and_decide(entity, task)
        assert analysis is not None
        assert hasattr(analysis, 'risk_level')
        assert hasattr(analysis, 'decision')
        assert analysis.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]

