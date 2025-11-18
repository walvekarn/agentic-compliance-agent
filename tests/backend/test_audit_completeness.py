"""Test cases for audit trail completeness"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.agent.audit_service import AuditService
from backend.agent.decision_engine import DecisionEngine
from backend.agent.risk_models import (
    EntityContext,
    TaskContext,
    EntityType,
    IndustryCategory,
    Jurisdiction,
    TaskCategory
)
from backend.db.models import AuditTrail


class TestAuditTrailCompleteness:
    """Test that audit trail captures all required information"""
    
    @pytest.fixture
    def decision_engine(self):
        """Create decision engine instance"""
        return DecisionEngine()
    
    def test_audit_trail_has_timestamp(self, db_session, decision_engine):
        """Test that every audit entry has a timestamp"""
        entity = EntityContext(
            name="Timestamp Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Test task for timestamp",
            category=TaskCategory.POLICY_REVIEW
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.timestamp is not None
        assert isinstance(audit_entry.timestamp, datetime)
        assert audit_entry.timestamp <= datetime.utcnow()
    
    def test_audit_trail_has_task_description(self, db_session, decision_engine):
        """Test that task description is captured"""
        entity = EntityContext(
            name="Description Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task_description = "Review and update data privacy policy for GDPR compliance"
        task = TaskContext(
            description=task_description,
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.task_description is not None
        assert audit_entry.task_description == task_description
        assert len(audit_entry.task_description) > 0
    
    def test_audit_trail_has_reasoning_chain(self, db_session, decision_engine):
        """Test that complete reasoning chain is captured"""
        entity = EntityContext(
            name="Reasoning Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            employee_count=250,
            has_personal_data=True
        )
        
        task = TaskContext(
            description="Security audit for customer database",
            category=TaskCategory.SECURITY_AUDIT,
            affects_personal_data=True
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.reasoning_chain is not None
        assert isinstance(audit_entry.reasoning_chain, list)
        assert len(audit_entry.reasoning_chain) > 0
        
        # Reasoning should include key steps
        reasoning_text = " ".join(audit_entry.reasoning_chain)
        assert any(keyword in reasoning_text for keyword in ["RISK", "DECISION", "risk", "decision"])
    
    def test_audit_trail_has_confidence_score(self, db_session, decision_engine):
        """Test that confidence score is captured and valid"""
        entity = EntityContext(
            name="Confidence Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="General compliance question",
            category=TaskCategory.GENERAL_INQUIRY
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.confidence_score is not None
        assert isinstance(audit_entry.confidence_score, float)
        assert 0 <= audit_entry.confidence_score <= 1
    
    def test_audit_trail_has_decision_outcome(self, db_session, decision_engine):
        """Test that decision outcome is captured"""
        entity = EntityContext(
            name="Decision Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Test task for decision",
            category=TaskCategory.POLICY_REVIEW
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.decision_outcome is not None
        assert audit_entry.decision_outcome in ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
    
    def test_audit_trail_has_risk_factors(self, db_session, decision_engine):
        """Test that all risk factors are captured"""
        entity = EntityContext(
            name="Risk Factors Test Corp",
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
            affects_financial_data=True
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.risk_factors is not None
        assert isinstance(audit_entry.risk_factors, dict)
        
        # Check all required risk factors
        required_factors = [
            "jurisdiction_risk",
            "entity_risk",
            "task_risk",
            "data_sensitivity_risk",
            "regulatory_risk",
            "impact_risk",
            "overall_score"
        ]
        
        for factor in required_factors:
            assert factor in audit_entry.risk_factors
            assert isinstance(audit_entry.risk_factors[factor], (int, float))
            assert 0 <= audit_entry.risk_factors[factor] <= 1
    
    def test_audit_trail_has_recommendations(self, db_session, decision_engine):
        """Test that recommendations are captured"""
        entity = EntityContext(
            name="Recommendations Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Policy review task",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.recommendations is not None
        assert isinstance(audit_entry.recommendations, list)
        assert len(audit_entry.recommendations) > 0
    
    def test_audit_trail_preserves_entity_context(self, db_session, decision_engine):
        """Test that full entity context is preserved"""
        entity = EntityContext(
            name="Entity Context Test Corp",
            entity_type=EntityType.FINANCIAL_INSTITUTION,
            industry=IndustryCategory.FINANCIAL_SERVICES,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            employee_count=1500,
            annual_revenue=100000000.0,
            has_personal_data=True,
            is_regulated=True,
            previous_violations=1
        )
        
        task = TaskContext(
            description="Financial compliance review",
            category=TaskCategory.FINANCIAL_REPORTING
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.entity_context is not None
        assert isinstance(audit_entry.entity_context, dict)
        
        # Verify key entity attributes are preserved
        assert audit_entry.entity_context["name"] == "Entity Context Test Corp"
        assert audit_entry.entity_context["employee_count"] == 1500
        assert audit_entry.entity_context["annual_revenue"] == 100000000.0
        assert audit_entry.entity_context["is_regulated"] == True
        assert audit_entry.entity_context["previous_violations"] == 1
    
    def test_audit_trail_preserves_task_context(self, db_session, decision_engine):
        """Test that full task context is preserved"""
        entity = EntityContext(
            name="Task Context Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=200
        )
        
        task_description = "Update customer data processing procedures"
        task = TaskContext(
            description=task_description,
            category=TaskCategory.DATA_PRIVACY,
            affects_personal_data=True,
            affects_financial_data=False,
            involves_cross_border=True,
            regulatory_deadline=datetime.utcnow() + timedelta(days=30),
            potential_impact="Significant",
            stakeholder_count=5000
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        assert audit_entry.task_context is not None
        assert isinstance(audit_entry.task_context, dict)
        
        # Verify key task attributes are preserved
        assert audit_entry.task_context["description"] == task_description
        assert audit_entry.task_context["affects_personal_data"] == True
        assert audit_entry.task_context["affects_financial_data"] == False
        assert audit_entry.task_context["involves_cross_border"] == True
        assert audit_entry.task_context["potential_impact"] == "Significant"
        assert audit_entry.task_context["stakeholder_count"] == 5000
    
    def test_audit_trail_agent_type_captured(self, db_session, decision_engine):
        """Test that agent type is captured"""
        entity = EntityContext(
            name="Agent Type Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Test task",
            category=TaskCategory.GENERAL_INQUIRY
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # Test with different agent types
        audit_entry1 = AuditService.log_decision_analysis(
            db_session, analysis, "decision_engine"
        )
        assert audit_entry1.agent_type == "decision_engine"
        
        audit_entry2 = AuditService.log_decision_analysis(
            db_session, analysis, "openai_agent"
        )
        assert audit_entry2.agent_type == "openai_agent"
    
    def test_audit_trail_metadata_captured(self, db_session, decision_engine):
        """Test that custom metadata is captured"""
        entity = EntityContext(
            name="Metadata Test Corp",
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
        
        custom_metadata = {
            "api_endpoint": "/test/endpoint",
            "version": "v1",
            "user_id": "test_user_123",
            "custom_field": "custom_value"
        }
        
        audit_entry = AuditService.log_decision_analysis(
            db_session, analysis, "decision_engine", metadata=custom_metadata
        )
        
        assert audit_entry.meta_data is not None
        assert audit_entry.meta_data["api_endpoint"] == "/test/endpoint"
        assert audit_entry.meta_data["version"] == "v1"
        assert audit_entry.meta_data["user_id"] == "test_user_123"
        assert audit_entry.meta_data["custom_field"] == "custom_value"
    
    def test_audit_trail_escalation_reason_captured(self, db_session, decision_engine):
        """Test that escalation reason is captured when applicable"""
        entity = EntityContext(
            name="Escalation Test Corp",
            entity_type=EntityType.FINANCIAL_INSTITUTION,
            industry=IndustryCategory.FINANCIAL_SERVICES,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=5000,
            has_personal_data=True,
            is_regulated=True
        )
        
        task = TaskContext(
            description="Critical incident response",
            category=TaskCategory.INCIDENT_RESPONSE,
            affects_personal_data=True,
            affects_financial_data=True,
            potential_impact="Critical"
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        if audit_entry.decision_outcome == "ESCALATE":
            assert audit_entry.escalation_reason is not None
            assert len(audit_entry.escalation_reason) > 0
    
    def test_audit_trail_to_dict_method(self, db_session, decision_engine):
        """Test that to_dict method produces valid JSON"""
        entity = EntityContext(
            name="Dict Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Test task for dict conversion",
            category=TaskCategory.POLICY_REVIEW
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        audit_entry = AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        audit_dict = audit_entry.to_dict()
        
        # Verify dict structure
        assert isinstance(audit_dict, dict)
        assert "audit_id" in audit_dict
        assert "timestamp" in audit_dict
        assert "agent_type" in audit_dict
        assert "task" in audit_dict
        assert "entity" in audit_dict
        assert "decision" in audit_dict
        assert "reasoning_chain" in audit_dict
        
        # Verify nested structures
        assert isinstance(audit_dict["task"], dict)
        assert isinstance(audit_dict["entity"], dict)
        assert isinstance(audit_dict["decision"], dict)
        assert isinstance(audit_dict["reasoning_chain"], list)
        
        # Verify timestamp is ISO format string
        assert isinstance(audit_dict["timestamp"], str)
    
    def test_audit_trail_queryable_by_filters(self, db_session, decision_engine):
        """Test that audit entries can be queried by various filters"""
        # Create multiple audit entries with different characteristics
        entities_tasks = [
            (
                EntityContext(
                    name="Company A",
                    entity_type=EntityType.STARTUP,
                    industry=IndustryCategory.TECHNOLOGY,
                    jurisdictions=[Jurisdiction.US_FEDERAL],
                    employee_count=50
                ),
                TaskContext(
                    description="Task A",
                    category=TaskCategory.GENERAL_INQUIRY
                )
            ),
            (
                EntityContext(
                    name="Company B",
                    entity_type=EntityType.PRIVATE_COMPANY,
                    industry=IndustryCategory.FINANCIAL_SERVICES,
                    jurisdictions=[Jurisdiction.EU],
                    employee_count=500
                ),
                TaskContext(
                    description="Task B",
                    category=TaskCategory.SECURITY_AUDIT,
                    affects_personal_data=True
                )
            ),
            (
                EntityContext(
                    name="Company A",  # Same as first
                    entity_type=EntityType.STARTUP,
                    industry=IndustryCategory.TECHNOLOGY,
                    jurisdictions=[Jurisdiction.US_FEDERAL],
                    employee_count=50
                ),
                TaskContext(
                    description="Task C",
                    category=TaskCategory.POLICY_REVIEW
                )
            )
        ]
        
        for entity, task in entities_tasks:
            analysis = decision_engine.analyze_and_decide(entity, task)
            AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        # Query by entity name
        company_a_entries = AuditService.get_audit_trail(
            db_session, entity_name="Company A", limit=10
        )
        assert len(company_a_entries) >= 2
        assert all(e.entity_name == "Company A" for e in company_a_entries)
        
        # Query by agent type
        decision_engine_entries = AuditService.get_audit_trail(
            db_session, agent_type="decision_engine", limit=10
        )
        assert len(decision_engine_entries) >= 3
        assert all(e.agent_type == "decision_engine" for e in decision_engine_entries)
    
    def test_audit_trail_statistics_complete(self, db_session, decision_engine):
        """Test that statistics capture all necessary metrics"""
        # Create diverse set of decisions
        test_cases = [
            (EntityType.STARTUP, TaskCategory.GENERAL_INQUIRY),
            (EntityType.PRIVATE_COMPANY, TaskCategory.POLICY_REVIEW),
            (EntityType.FINANCIAL_INSTITUTION, TaskCategory.SECURITY_AUDIT),
        ]
        
        for entity_type, task_category in test_cases:
            entity = EntityContext(
                name=f"Stats Test {entity_type.value}",
                entity_type=entity_type,
                industry=IndustryCategory.TECHNOLOGY,
                jurisdictions=[Jurisdiction.US_FEDERAL],
                employee_count=100
            )
            
            task = TaskContext(
                description=f"Test task {task_category.value}",
                category=task_category
            )
            
            analysis = decision_engine.analyze_and_decide(entity, task)
            AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        # Get statistics
        stats = AuditService.get_audit_statistics(db_session)
        
        # Verify statistics structure
        assert "total_decisions" in stats
        assert "by_outcome" in stats
        assert "by_risk_level" in stats
        assert "by_agent_type" in stats
        assert "by_task_category" in stats
        assert "average_confidence" in stats
        assert "average_risk_score" in stats
        
        # Verify statistics values
        assert stats["total_decisions"] >= 3
        assert 0 <= stats["average_confidence"] <= 1
        assert 0 <= stats["average_risk_score"] <= 1
    
    def test_audit_trail_export_json(self, db_session, decision_engine):
        """Test that audit trail can be exported as JSON"""
        entity = EntityContext(
            name="Export Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100
        )
        
        task = TaskContext(
            description="Test task for export",
            category=TaskCategory.POLICY_REVIEW
        )
        
        analysis = decision_engine.analyze_and_decide(entity, task)
        AuditService.log_decision_analysis(db_session, analysis, "decision_engine")
        
        # Export as JSON
        json_export = AuditService.export_audit_trail_json(db_session, limit=10)
        
        assert isinstance(json_export, list)
        assert len(json_export) > 0
        
        # Verify each entry is a valid dict
        for entry in json_export:
            assert isinstance(entry, dict)
            assert "audit_id" in entry
            assert "timestamp" in entry
            assert "reasoning_chain" in entry
            assert "decision" in entry

