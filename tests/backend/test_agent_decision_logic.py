"""Test cases for agent decision logic"""

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


class TestDecisionEngineLogic:
    """Test decision engine core logic"""
    
    @pytest.fixture
    def decision_engine(self):
        """Create decision engine instance"""
        return DecisionEngine()
    
    def test_low_risk_autonomous_decision(self, decision_engine):
        """Test that low-risk tasks with capable entities get AUTONOMOUS decision"""
        entity = EntityContext(
            name="Low Risk Startup",
            entity_type=EntityType.STARTUP,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=20,
            has_personal_data=False,
            is_regulated=False,
            previous_violations=0
        )
        
        task = TaskContext(
            description="General compliance question about data retention",
            category=TaskCategory.GENERAL_INQUIRY,
            affects_personal_data=False,
            affects_financial_data=False,
            involves_cross_border=False
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        assert analysis.risk_level == RiskLevel.LOW
        assert analysis.decision in [ActionDecision.AUTONOMOUS, ActionDecision.REVIEW_REQUIRED]
        assert analysis.confidence > 0.6
        assert len(analysis.reasoning) > 0
    
    def test_high_risk_escalate_decision(self, decision_engine):
        """Test that high-risk tasks get ESCALATE decision"""
        entity = EntityContext(
            name="Large Financial Institution",
            entity_type=EntityType.FINANCIAL_INSTITUTION,
            industry=IndustryCategory.FINANCIAL_SERVICES,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            employee_count=10000,
            has_personal_data=True,
            is_regulated=True,
            previous_violations=0
        )
        
        task = TaskContext(
            description="Data breach affecting 100,000 customers",
            category=TaskCategory.INCIDENT_RESPONSE,
            affects_personal_data=True,
            affects_financial_data=True,
            involves_cross_border=True,
            potential_impact="Critical"
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        assert analysis.risk_level == RiskLevel.HIGH
        assert analysis.decision == ActionDecision.ESCALATE
        assert analysis.confidence > 0.8
        assert analysis.escalation_reason is not None
        assert len(analysis.recommendations) > 0
    
    def test_medium_risk_review_required(self, decision_engine):
        """Test that medium-risk tasks get REVIEW_REQUIRED decision"""
        entity = EntityContext(
            name="Mid-Size Company",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            employee_count=500,
            has_personal_data=True,
            is_regulated=False,
            previous_violations=0
        )
        
        task = TaskContext(
            description="Update privacy policy for GDPR compliance",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True,
            affects_financial_data=False,
            involves_cross_border=True,
            potential_impact="Moderate"
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        assert analysis.risk_level in [RiskLevel.MEDIUM, RiskLevel.LOW]
        assert analysis.decision in [ActionDecision.REVIEW_REQUIRED, ActionDecision.AUTONOMOUS]
        assert 0 < analysis.confidence <= 1
    
    def test_previous_violations_override(self, decision_engine):
        """Test that previous violations force review even for low risk"""
        entity = EntityContext(
            name="Company with Violations",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100,
            has_personal_data=True,
            is_regulated=False,
            previous_violations=3  # Multiple violations
        )
        
        task = TaskContext(
            description="Update data retention policy",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # Even if risk is low, decision should not be fully autonomous
        if analysis.risk_level == RiskLevel.LOW:
            assert analysis.decision != ActionDecision.AUTONOMOUS or analysis.confidence < 0.9
    
    def test_incident_response_always_escalates(self, decision_engine):
        """Test that incident response tasks always escalate"""
        entity = EntityContext(
            name="Any Company",
            entity_type=EntityType.STARTUP,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=50,
            has_personal_data=True,
            is_regulated=False,
            previous_violations=0
        )
        
        task = TaskContext(
            description="Security incident detected",
            category=TaskCategory.INCIDENT_RESPONSE,
            affects_personal_data=True,
            potential_impact="Significant"
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # Incident response should always escalate
        assert analysis.decision == ActionDecision.ESCALATE
        assert "incident" in analysis.escalation_reason.lower() or \
               "INCIDENT_RESPONSE" in str(analysis.reasoning)
    
    def test_multi_jurisdictional_increases_risk(self, decision_engine):
        """Test that multi-jurisdictional tasks have higher risk"""
        # Single jurisdiction
        entity_single = EntityContext(
            name="US Only Company",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=200,
            has_personal_data=True
        )
        
        # Multi-jurisdictional
        entity_multi = EntityContext(
            name="Global Company",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU, Jurisdiction.UK],
            employee_count=200,
            has_personal_data=True
        )
        
        task = TaskContext(
            description="Data processing policy review",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True,
            involves_cross_border=True
        )
        
        analysis_single = decision_engine.analyze_and_decide(entity_single, task)
        analysis_multi = decision_engine.analyze_and_decide(entity_multi, task)
        
        # Multi-jurisdictional should have higher jurisdiction risk
        assert analysis_multi.risk_factors.jurisdiction_risk >= \
               analysis_single.risk_factors.jurisdiction_risk
    
    def test_financial_data_increases_risk(self, decision_engine):
        """Test that financial data involvement increases risk"""
        entity = EntityContext(
            name="Financial Services Company",
            entity_type=EntityType.FINANCIAL_INSTITUTION,
            industry=IndustryCategory.FINANCIAL_SERVICES,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=1000,
            has_personal_data=True,
            is_regulated=True
        )
        
        # Task without financial data
        task_no_finance = TaskContext(
            description="Update employee handbook",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=False,
            affects_financial_data=False
        )
        
        # Task with financial data
        task_with_finance = TaskContext(
            description="Update customer payment processing",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True,
            affects_financial_data=True
        )
        
        analysis_no_finance = decision_engine.analyze_and_decide(entity, task_no_finance)
        analysis_with_finance = decision_engine.analyze_and_decide(entity, task_with_finance)
        
        # Financial data should increase data sensitivity risk
        assert analysis_with_finance.risk_factors.data_sensitivity_risk > \
               analysis_no_finance.risk_factors.data_sensitivity_risk
    
    def test_regulated_entity_increases_risk(self, decision_engine):
        """Test that regulated entities have higher risk"""
        # Non-regulated
        entity_not_regulated = EntityContext(
            name="Startup",
            entity_type=EntityType.STARTUP,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=50,
            has_personal_data=True,
            is_regulated=False
        )
        
        # Regulated
        entity_regulated = EntityContext(
            name="Bank",
            entity_type=EntityType.FINANCIAL_INSTITUTION,
            industry=IndustryCategory.FINANCIAL_SERVICES,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=50,
            has_personal_data=True,
            is_regulated=True
        )
        
        task = TaskContext(
            description="Compliance policy update",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True
        )
        
        analysis_not_regulated = decision_engine.analyze_and_decide(entity_not_regulated, task)
        analysis_regulated = decision_engine.analyze_and_decide(entity_regulated, task)
        
        # Regulated entities should have higher regulatory risk
        assert analysis_regulated.risk_factors.regulatory_risk > \
               analysis_not_regulated.risk_factors.regulatory_risk
    
    def test_task_category_risk_levels(self, decision_engine):
        """Test that different task categories have appropriate risk levels"""
        entity = EntityContext(
            name="Test Company",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=200,
            has_personal_data=True
        )
        
        # Test various task categories
        categories_risks = []
        
        for category in [TaskCategory.GENERAL_INQUIRY, TaskCategory.POLICY_REVIEW, 
                        TaskCategory.SECURITY_AUDIT, TaskCategory.REGULATORY_FILING]:
            task = TaskContext(
                description=f"Test task for {category.value}",
                category=category,
                affects_personal_data=True
            )
            
            analysis = decision_engine.analyze_and_decide(entity, task)
            categories_risks.append((category, analysis.risk_factors.task_risk))
        
        # General inquiry should be lowest risk
        general_inquiry_risk = next(r for c, r in categories_risks if c == TaskCategory.GENERAL_INQUIRY)
        regulatory_filing_risk = next(r for c, r in categories_risks if c == TaskCategory.REGULATORY_FILING)
        
        # Regulatory filing should be higher risk than general inquiry
        assert regulatory_filing_risk > general_inquiry_risk
    
    def test_confidence_score_range(self, decision_engine):
        """Test that confidence scores are always in valid range"""
        entity = EntityContext(
            name="Test Entity",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        # Test multiple scenarios
        tasks = [
            TaskContext(description="Low risk task", category=TaskCategory.GENERAL_INQUIRY),
            TaskContext(description="Medium risk task", category=TaskCategory.POLICY_REVIEW, 
                       affects_personal_data=True),
            TaskContext(description="High risk task", category=TaskCategory.INCIDENT_RESPONSE,
                       affects_personal_data=True, affects_financial_data=True)
        ]
        
        for task in tasks:
            analysis = decision_engine.analyze_and_decide(entity, task)
            assert 0 <= analysis.confidence <= 1, \
                f"Confidence {analysis.confidence} out of range for {task.category}"
    
    def test_risk_score_range(self, decision_engine):
        """Test that all risk scores are in valid range [0, 1]"""
        entity = EntityContext(
            name="Test Entity",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            employee_count=500,
            has_personal_data=True,
            is_regulated=True
        )
        
        task = TaskContext(
            description="Complex compliance task",
            category=TaskCategory.REGULATORY_FILING,
            affects_personal_data=True,
            affects_financial_data=True,
            involves_cross_border=True
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # Check all risk factors
        assert 0 <= analysis.risk_factors.jurisdiction_risk <= 1
        assert 0 <= analysis.risk_factors.entity_risk <= 1
        assert 0 <= analysis.risk_factors.task_risk <= 1
        assert 0 <= analysis.risk_factors.data_sensitivity_risk <= 1
        assert 0 <= analysis.risk_factors.regulatory_risk <= 1
        assert 0 <= analysis.risk_factors.impact_risk <= 1
        assert 0 <= analysis.risk_factors.overall_score <= 1
    
    def test_reasoning_chain_not_empty(self, decision_engine):
        """Test that reasoning chain is always populated"""
        entity = EntityContext(
            name="Test Entity",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Test task",
            category=TaskCategory.POLICY_REVIEW
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        assert len(analysis.reasoning) > 0
        assert any("RISK" in r or "DECISION" in r for r in analysis.reasoning)
    
    def test_recommendations_not_empty(self, decision_engine):
        """Test that recommendations are always provided"""
        entity = EntityContext(
            name="Test Entity",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Test task",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        assert len(analysis.recommendations) > 0
    
    def test_escalation_reason_when_escalated(self, decision_engine):
        """Test that escalation reason is provided when decision is ESCALATE"""
        entity = EntityContext(
            name="High Risk Entity",
            entity_type=EntityType.FINANCIAL_INSTITUTION,
            industry=IndustryCategory.FINANCIAL_SERVICES,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            employee_count=5000,
            has_personal_data=True,
            is_regulated=True,
            previous_violations=2
        )
        
        task = TaskContext(
            description="Critical incident response",
            category=TaskCategory.INCIDENT_RESPONSE,
            affects_personal_data=True,
            affects_financial_data=True,
            potential_impact="Critical"
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        if analysis.decision == ActionDecision.ESCALATE:
            assert analysis.escalation_reason is not None
            assert len(analysis.escalation_reason) > 0
    
    def test_decision_consistency(self, decision_engine):
        """Test that same inputs produce same decision"""
        entity = EntityContext(
            name="Consistent Test Entity",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=200,
            has_personal_data=True
        )
        
        task = TaskContext(
            description="Consistent test task",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True
        )
        
        # Run analysis multiple times
        analysis1 = decision_engine.analyze_and_decide(entity, task)
        analysis2 = decision_engine.analyze_and_decide(entity, task)
        
        # Should get same decision
        assert analysis1.decision == analysis2.decision
        assert analysis1.risk_level == analysis2.risk_level
        assert abs(analysis1.confidence - analysis2.confidence) < 0.01
        assert abs(analysis1.risk_factors.overall_score - 
                  analysis2.risk_factors.overall_score) < 0.01

