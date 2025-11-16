"""Test cases for audit trail functionality"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.agent.audit_service import AuditService
from src.agent.decision_engine import DecisionEngine
from src.agent.risk_models import (
    EntityContext,
    TaskContext,
    EntityType,
    IndustryCategory,
    Jurisdiction,
    TaskCategory
)
from src.db.models import AuditTrail


class TestAuditTrailModel:
    """Test the AuditTrail database model"""
    
    def test_audit_trail_creation(self, db_session: Session):
        """Test creating an audit trail entry"""
        audit_entry = AuditTrail(
            timestamp=datetime.utcnow(),
            agent_type="decision_engine",
            task_description="Test task",
            task_category="DATA_PRIVACY",
            entity_name="Test Corp",
            entity_type="PRIVATE_COMPANY",
            decision_outcome="REVIEW_REQUIRED",
            confidence_score=0.85,
            risk_level="MEDIUM",
            risk_score=0.55,
            reasoning_chain=["Step 1", "Step 2"],
            risk_factors={"jurisdiction_risk": 0.5},
            recommendations=["Review carefully"],
            metadata={"test": True}
        )
        
        db_session.add(audit_entry)
        db_session.commit()
        db_session.refresh(audit_entry)
        
        assert audit_entry.id is not None
        assert audit_entry.agent_type == "decision_engine"
        assert audit_entry.decision_outcome == "REVIEW_REQUIRED"
        assert audit_entry.confidence_score == 0.85
    
    def test_audit_trail_to_dict(self, db_session: Session):
        """Test converting audit trail to dictionary"""
        audit_entry = AuditTrail(
            timestamp=datetime.utcnow(),
            agent_type="openai_agent",
            task_description="Test query",
            decision_outcome="RESPONSE_PROVIDED",
            confidence_score=0.75,
            reasoning_chain=["Processed query"]
        )
        
        db_session.add(audit_entry)
        db_session.commit()
        db_session.refresh(audit_entry)
        
        audit_dict = audit_entry.to_dict()
        
        assert isinstance(audit_dict, dict)
        assert audit_dict["audit_id"] == audit_entry.id
        assert audit_dict["agent_type"] == "openai_agent"
        assert audit_dict["decision"]["confidence_score"] == 0.75
        assert isinstance(audit_dict["timestamp"], str)


class TestAuditService:
    """Test the AuditService functionality"""
    
    def test_log_decision_analysis(self, db_session: Session):
        """Test logging a DecisionAnalysis to audit trail"""
        # Create test entity and task
        entity = EntityContext(
            name="Test Company",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=100,
            has_personal_data=True
        )
        
        task = TaskContext(
            description="Review data privacy policy",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True
        )
        
        # Run decision engine analysis
        decision_engine = DecisionEngine()
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # Log to audit trail
        audit_entry = AuditService.log_decision_analysis(
            db=db_session,
            analysis=analysis,
            agent_type="decision_engine",
            metadata={"test": "log_decision_analysis"}
        )
        
        assert audit_entry.id is not None
        assert audit_entry.agent_type == "decision_engine"
        assert audit_entry.entity_name == "Test Company"
        assert audit_entry.task_category == "POLICY_REVIEW"
        assert audit_entry.decision_outcome in ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
        assert 0 <= audit_entry.confidence_score <= 1
        assert len(audit_entry.reasoning_chain) > 0
        assert audit_entry.risk_factors is not None
        assert "jurisdiction_risk" in audit_entry.risk_factors
    
    def test_log_custom_decision(self, db_session: Session):
        """Test logging a custom decision"""
        audit_entry = AuditService.log_custom_decision(
            db=db_session,
            task_description="Custom compliance query",
            decision_outcome="RESPONSE_PROVIDED",
            confidence_score=0.80,
            reasoning_chain=["Step 1", "Step 2", "Step 3"],
            agent_type="openai_agent",
            task_category="GENERAL_INQUIRY",
            entity_name="Acme Corp",
            metadata={"custom": True}
        )
        
        assert audit_entry.id is not None
        assert audit_entry.agent_type == "openai_agent"
        assert audit_entry.task_description == "Custom compliance query"
        assert audit_entry.decision_outcome == "RESPONSE_PROVIDED"
        assert audit_entry.confidence_score == 0.80
        assert len(audit_entry.reasoning_chain) == 3
    
    def test_get_audit_trail(self, db_session: Session):
        """Test retrieving audit trail entries"""
        # Create multiple audit entries
        for i in range(5):
            AuditService.log_custom_decision(
                db=db_session,
                task_description=f"Task {i}",
                decision_outcome="REVIEW_REQUIRED",
                confidence_score=0.7 + (i * 0.05),
                reasoning_chain=[f"Reason {i}"],
                agent_type="decision_engine"
            )
        
        # Retrieve all entries
        entries = AuditService.get_audit_trail(db=db_session, limit=10)
        
        assert len(entries) >= 5
        assert all(isinstance(entry, AuditTrail) for entry in entries)
        
        # Verify ordering (newest first)
        if len(entries) > 1:
            for i in range(len(entries) - 1):
                assert entries[i].timestamp >= entries[i + 1].timestamp
    
    def test_get_audit_trail_with_filters(self, db_session: Session):
        """Test retrieving audit trail with filters"""
        # Create entries with different attributes
        AuditService.log_custom_decision(
            db=db_session,
            task_description="High risk task",
            decision_outcome="ESCALATE",
            confidence_score=0.9,
            reasoning_chain=["High risk"],
            agent_type="decision_engine",
            risk_level="HIGH",
            entity_name="Company A"
        )
        
        AuditService.log_custom_decision(
            db=db_session,
            task_description="Low risk task",
            decision_outcome="AUTONOMOUS",
            confidence_score=0.85,
            reasoning_chain=["Low risk"],
            agent_type="decision_engine",
            risk_level="LOW",
            entity_name="Company B"
        )
        
        # Filter by risk level
        high_risk_entries = AuditService.get_audit_trail(
            db=db_session,
            risk_level="HIGH",
            limit=10
        )
        
        assert len(high_risk_entries) >= 1
        assert all(entry.risk_level == "HIGH" for entry in high_risk_entries)
        
        # Filter by decision outcome
        escalate_entries = AuditService.get_audit_trail(
            db=db_session,
            decision_outcome="ESCALATE",
            limit=10
        )
        
        assert len(escalate_entries) >= 1
        assert all(entry.decision_outcome == "ESCALATE" for entry in escalate_entries)
        
        # Filter by entity name
        company_a_entries = AuditService.get_audit_trail(
            db=db_session,
            entity_name="Company A",
            limit=10
        )
        
        assert len(company_a_entries) >= 1
        assert all(entry.entity_name == "Company A" for entry in company_a_entries)
    
    def test_get_audit_trail_with_date_filters(self, db_session: Session):
        """Test retrieving audit trail with date filters"""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Create an entry
        audit_entry = AuditService.log_custom_decision(
            db=db_session,
            task_description="Test task",
            decision_outcome="REVIEW_REQUIRED",
            confidence_score=0.75,
            reasoning_chain=["Test"]
        )
        
        # Filter by date range (should include the entry)
        entries = AuditService.get_audit_trail(
            db=db_session,
            start_date=yesterday,
            end_date=tomorrow,
            limit=10
        )
        
        assert len(entries) >= 1
        assert any(entry.id == audit_entry.id for entry in entries)
        
        # Filter with future start date (should exclude the entry)
        future_entries = AuditService.get_audit_trail(
            db=db_session,
            start_date=tomorrow,
            limit=10
        )
        
        assert not any(entry.id == audit_entry.id for entry in future_entries)
    
    def test_get_audit_entry(self, db_session: Session):
        """Test retrieving a specific audit entry"""
        # Create an entry
        audit_entry = AuditService.log_custom_decision(
            db=db_session,
            task_description="Specific task",
            decision_outcome="AUTONOMOUS",
            confidence_score=0.88,
            reasoning_chain=["Specific reason"]
        )
        
        # Retrieve it by ID
        retrieved_entry = AuditService.get_audit_entry(db=db_session, audit_id=audit_entry.id)
        
        assert retrieved_entry is not None
        assert retrieved_entry.id == audit_entry.id
        assert retrieved_entry.task_description == "Specific task"
        assert retrieved_entry.confidence_score == 0.88
    
    def test_get_audit_statistics(self, db_session: Session):
        """Test getting audit trail statistics"""
        # Create various entries
        AuditService.log_custom_decision(
            db=db_session,
            task_description="Task 1",
            decision_outcome="AUTONOMOUS",
            confidence_score=0.9,
            reasoning_chain=["Reason 1"],
            risk_level="LOW",
            risk_score=0.3,
            agent_type="decision_engine",
            task_category="POLICY_REVIEW"
        )
        
        AuditService.log_custom_decision(
            db=db_session,
            task_description="Task 2",
            decision_outcome="ESCALATE",
            confidence_score=0.85,
            reasoning_chain=["Reason 2"],
            risk_level="HIGH",
            risk_score=0.8,
            agent_type="decision_engine",
            task_category="SECURITY_AUDIT"
        )
        
        AuditService.log_custom_decision(
            db=db_session,
            task_description="Task 3",
            decision_outcome="REVIEW_REQUIRED",
            confidence_score=0.75,
            reasoning_chain=["Reason 3"],
            risk_level="MEDIUM",
            risk_score=0.5,
            agent_type="openai_agent",
            task_category="GENERAL_INQUIRY"
        )
        
        # Get statistics
        stats = AuditService.get_audit_statistics(db=db_session)
        
        assert stats["total_decisions"] >= 3
        assert "by_outcome" in stats
        assert "by_risk_level" in stats
        assert "by_agent_type" in stats
        assert "by_task_category" in stats
        assert "average_confidence" in stats
        assert "average_risk_score" in stats
        
        # Verify counts
        assert stats["by_outcome"].get("AUTONOMOUS", 0) >= 1
        assert stats["by_outcome"].get("ESCALATE", 0) >= 1
        assert stats["by_outcome"].get("REVIEW_REQUIRED", 0) >= 1
        
        # Verify averages
        assert 0 <= stats["average_confidence"] <= 1
        assert 0 <= stats["average_risk_score"] <= 1
    
    def test_export_audit_trail_json(self, db_session: Session):
        """Test exporting audit trail as JSON"""
        # Create test entries
        for i in range(3):
            AuditService.log_custom_decision(
                db=db_session,
                task_description=f"Export task {i}",
                decision_outcome="REVIEW_REQUIRED",
                confidence_score=0.8,
                reasoning_chain=[f"Export reason {i}"],
                agent_type="decision_engine"
            )
        
        # Export to JSON
        json_data = AuditService.export_audit_trail_json(db=db_session, limit=10)
        
        assert isinstance(json_data, list)
        assert len(json_data) >= 3
        
        # Verify JSON structure
        for entry_dict in json_data:
            assert "audit_id" in entry_dict
            assert "timestamp" in entry_dict
            assert "agent_type" in entry_dict
            assert "task" in entry_dict
            assert "decision" in entry_dict
            assert "reasoning_chain" in entry_dict
            
            # Verify nested structure
            assert "description" in entry_dict["task"]
            assert "outcome" in entry_dict["decision"]
            assert "confidence_score" in entry_dict["decision"]


class TestAuditTrailIntegration:
    """Integration tests for audit trail with decision engine"""
    
    def test_decision_engine_audit_logging(self, db_session: Session):
        """Test that decision engine automatically logs to audit trail"""
        entity = EntityContext(
            name="Integration Test Corp",
            entity_type=EntityType.PRIVATE_COMPANY,
            industry=IndustryCategory.FINANCIAL_SERVICES,
            jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
            employee_count=500,
            annual_revenue=10_000_000,
            has_personal_data=True,
            is_regulated=True
        )
        
        task = TaskContext(
            description="Process customer financial data",
            category=TaskCategory.FINANCIAL_REPORTING,
            affects_personal_data=True,
            affects_financial_data=True
        )
        
        # Run analysis
        decision_engine = DecisionEngine()
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # Log to audit trail
        audit_entry = AuditService.log_decision_analysis(
            db=db_session,
            analysis=analysis,
            agent_type="decision_engine"
        )
        
        # Verify complete audit trail entry
        assert audit_entry.entity_name == "Integration Test Corp"
        assert audit_entry.task_category == "FINANCIAL_REPORTING"
        assert audit_entry.decision_outcome in ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
        assert audit_entry.risk_level in ["LOW", "MEDIUM", "HIGH"]
        assert audit_entry.risk_factors is not None
        assert audit_entry.recommendations is not None
        assert len(audit_entry.reasoning_chain) > 0
        
        # Verify we can retrieve it
        retrieved = AuditService.get_audit_entry(db=db_session, audit_id=audit_entry.id)
        assert retrieved is not None
        assert retrieved.id == audit_entry.id
    
    def test_multiple_decisions_tracking(self, db_session: Session):
        """Test tracking multiple decisions over time"""
        entity = EntityContext(
            name="Multi Decision Corp",
            entity_type=EntityType.STARTUP,
            industry=IndustryCategory.TECHNOLOGY,
            jurisdictions=[Jurisdiction.US_FEDERAL],
            employee_count=50
        )
        
        tasks = [
            TaskContext(
                description="General compliance question",
                category=TaskCategory.GENERAL_INQUIRY
            ),
            TaskContext(
                description="Review privacy policy",
                category=TaskCategory.POLICY_REVIEW,
                affects_personal_data=True
            ),
            TaskContext(
                description="Security audit",
                category=TaskCategory.SECURITY_AUDIT,
                potential_impact="Critical"
            )
        ]
        
        decision_engine = DecisionEngine()
        audit_ids = []
        
        # Process multiple tasks
        for task in tasks:
            analysis = decision_engine.analyze_and_decide(entity, task)
            audit_entry = AuditService.log_decision_analysis(
                db=db_session,
                analysis=analysis
            )
            audit_ids.append(audit_entry.id)
        
        # Verify all were logged
        assert len(audit_ids) == 3
        
        # Retrieve by entity name
        entity_entries = AuditService.get_audit_trail(
            db=db_session,
            entity_name="Multi Decision Corp",
            limit=10
        )
        
        assert len(entity_entries) >= 3
        
        # Verify different task categories
        categories = {entry.task_category for entry in entity_entries}
        assert "GENERAL_INQUIRY" in categories
        assert "POLICY_REVIEW" in categories
        assert "SECURITY_AUDIT" in categories

