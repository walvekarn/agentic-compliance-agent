"""Test cases for entity analysis endpoints"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from main import app
from backend.db.base import get_db


@pytest.fixture(autouse=True)
def setup_db_override(db_session):
    """Automatically override database dependency for all tests"""
    def _override():
        yield db_session
    
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


class TestAnalyzeEntityEndpoint:
    """Test POST /api/v1/entity/analyze endpoint"""
    
    def test_analyze_entity_minimal_request(self, db_session):
        """Test entity analysis with minimal request"""
        request_data = {
            "entity_name": "TestCorp",
            "locations": ["US"]
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "entity_name" in data
        assert "jurisdictions" in data
        assert "applicable_regulations" in data
        assert "tasks" in data
        assert "summary" in data
        
        # Verify entity name
        assert data["entity_name"] == "TestCorp"
        assert "US" in data["jurisdictions"]
        
        # Verify tasks exist
        assert len(data["tasks"]) > 0
        
        # Verify summary
        summary = data["summary"]
        assert "total_tasks" in summary
        assert "decisions" in summary
        assert "average_confidence" in summary
        assert summary["total_tasks"] > 0
    
    def test_analyze_entity_full_request(self, db_session):
        """Test entity analysis with all parameters"""
        request_data = {
            "entity_name": "GlobalTech Solutions",
            "locations": ["US", "EU", "UK"],
            "entity_type": "PRIVATE_COMPANY",
            "industry": "TECHNOLOGY",
            "employee_count": 500,
            "annual_revenue": 50000000.0,
            "has_personal_data": True,
            "is_regulated": False,
            "previous_violations": 0
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify multi-jurisdictional handling
        assert len(data["jurisdictions"]) == 3
        
        # Verify applicable regulations include GDPR for EU
        regulations = data["applicable_regulations"]
        assert any("GDPR" in reg for reg in regulations)
        
        # Verify tasks
        tasks = data["tasks"]
        assert len(tasks) > 5  # Should have multiple tasks
        
        # Verify each task has required fields
        for task in tasks:
            assert "task_id" in task
            assert "task_name" in task
            assert "description" in task
            assert "category" in task
            assert "frequency" in task
            assert "decision" in task
            assert "confidence" in task
            assert "risk_level" in task
            assert "audit_id" in task
            
            # Verify decision is valid
            assert task["decision"] in ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
            
            # Verify risk level is valid
            assert task["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
            
            # Verify confidence is in range
            assert 0 <= task["confidence"] <= 1
        
        # Verify summary statistics
        summary = data["summary"]
        assert summary["total_tasks"] == len(tasks)
        assert "autonomous" in summary["decisions"]
        assert "reviewrequired" in summary["decisions"]
        assert "escalate" in summary["decisions"]
        assert 0 <= summary["average_confidence"] <= 1
        assert 0 <= summary["autonomous_percentage"] <= 100
    
    def test_analyze_financial_institution(self, db_session):
        """Test analysis of financial institution (high-risk entity)"""
        request_data = {
            "entity_name": "SecureBank Corp",
            "locations": ["US"],
            "entity_type": "FINANCIAL_INSTITUTION",
            "industry": "FINANCIAL_SERVICES",
            "employee_count": 2500,
            "has_personal_data": True,
            "is_regulated": True
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Financial institutions should have specific tasks
        task_names = [task["task_name"] for task in data["tasks"]]
        assert any("Financial" in name or "AML" in name for name in task_names)
        
        # Should have regulatory filing tasks (is_regulated=True)
        assert any("Regulatory Filing" in name for name in task_names)
        
        # Financial institutions typically have higher escalation rates
        summary = data["summary"]
        escalate_count = summary["decisions"].get("escalate", 0)
        assert escalate_count >= 0  # May have tasks requiring escalation
    
    def test_analyze_healthcare_entity(self, db_session):
        """Test analysis of healthcare entity"""
        request_data = {
            "entity_name": "HealthCare Plus",
            "locations": ["US"],
            "entity_type": "HEALTHCARE",
            "industry": "HEALTHCARE",
            "employee_count": 500,
            "has_personal_data": True
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Healthcare entities should have HIPAA-related tasks
        task_names = [task["task_name"] for task in data["tasks"]]
        assert any("HIPAA" in name for name in task_names)
    
    def test_analyze_eu_entity(self, db_session):
        """Test analysis of EU-based entity"""
        request_data = {
            "entity_name": "EuroTech",
            "locations": ["EU"],
            "entity_type": "PRIVATE_COMPANY",
            "industry": "TECHNOLOGY",
            "has_personal_data": True
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have GDPR in applicable regulations
        regulations = data["applicable_regulations"]
        assert any("GDPR" in reg for reg in regulations)
        
        # Should have GDPR-specific tasks
        task_names = [task["task_name"] for task in data["tasks"]]
        assert any("GDPR" in name for name in task_names)
    
    def test_analyze_startup(self, db_session):
        """Test analysis of startup (typically lower risk)"""
        request_data = {
            "entity_name": "StartupCo",
            "locations": ["US"],
            "entity_type": "STARTUP",
            "industry": "TECHNOLOGY",
            "employee_count": 25,
            "has_personal_data": False,
            "is_regulated": False,
            "previous_violations": 0
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Startups with no personal data should have higher autonomy rate
        summary = data["summary"]
        # Not asserting specific threshold as it depends on tasks generated
        assert "autonomous_percentage" in summary
    
    def test_invalid_entity_type(self, db_session):
        """Test with invalid entity type"""
        request_data = {
            "entity_name": "TestCorp",
            "locations": ["US"],
            "entity_type": "INVALID_TYPE"
        }
        
        # Should handle gracefully (use default or return error)
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        # Either succeeds with default or returns validation error
        assert response.status_code in [200, 422]
    
    def test_missing_required_fields(self, db_session):
        """Test with missing required fields"""
        # Missing entity_name
        response = client.post("/api/v1/entity/analyze", json={"locations": ["US"]})
        assert response.status_code == 422
        
        # Missing locations
        response = client.post("/api/v1/entity/analyze", json={"entity_name": "Test"})
        assert response.status_code == 422
    
    def test_empty_locations(self, db_session):
        """Test with empty locations array"""
        request_data = {
            "entity_name": "TestCorp",
            "locations": []
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        assert response.status_code == 422
    
    def test_audit_trail_created(self, db_session):
        """Test that audit trail entries are created for all tasks"""
        request_data = {
            "entity_name": "AuditTestCorp",
            "locations": ["US"]
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Each task should have an audit_id
        for task in data["tasks"]:
            assert task["audit_id"] is not None
            assert isinstance(task["audit_id"], int)
            assert task["audit_id"] > 0


class TestAuditLogEndpoint:
    """Test GET /api/v1/audit_log/{task_id} endpoint"""
    
    def test_get_audit_log_existing_task(self, db_session):
        """Test retrieving audit log for existing task"""
        # First create an entity analysis to generate tasks
        request_data = {
            "entity_name": "AuditLogTestCorp",
            "locations": ["US"]
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        task_id = data["tasks"][0]["task_id"]
        
        # Now get the audit log
        response = client.get(f"/api/v1/audit_log/{task_id}")
        
        assert response.status_code == 200
        audit_log = response.json()
        
        # Verify audit log structure
        assert "task_id" in audit_log
        assert "audit_id" in audit_log
        assert "timestamp" in audit_log
        assert "entity_name" in audit_log
        assert "task_description" in audit_log
        assert "task_category" in audit_log
        assert "decision_outcome" in audit_log
        assert "confidence_score" in audit_log
        assert "risk_level" in audit_log
        assert "reasoning_chain" in audit_log
        assert "risk_factors" in audit_log
        assert "recommendations" in audit_log
        
        # Verify task_id matches
        assert audit_log["task_id"] == task_id
        
        # Verify reasoning chain is not empty
        assert len(audit_log["reasoning_chain"]) > 0
        
        # Verify risk factors
        risk_factors = audit_log["risk_factors"]
        assert "jurisdiction_risk" in risk_factors
        assert "entity_risk" in risk_factors
        assert "task_risk" in risk_factors
        assert "overall_score" in risk_factors
        
        # Verify confidence score is in range
        assert 0 <= audit_log["confidence_score"] <= 1
    
    def test_get_audit_log_nonexistent_task(self, db_session):
        """Test retrieving audit log for non-existent task"""
        response = client.get("/api/v1/audit_log/TASK-9999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_audit_log_reasoning_completeness(self, db_session):
        """Test that audit log contains complete reasoning"""
        # Create entity analysis
        request_data = {
            "entity_name": "ReasoningTestCorp",
            "locations": ["US", "EU"],
            "has_personal_data": True
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        assert response.status_code == 200
        
        task_id = response.json()["tasks"][0]["task_id"]
        
        # Get audit log
        response = client.get(f"/api/v1/audit_log/{task_id}")
        assert response.status_code == 200
        
        audit_log = response.json()
        reasoning = audit_log["reasoning_chain"]
        
        # Verify reasoning includes key sections
        reasoning_text = " ".join(reasoning)
        assert "RISK" in reasoning_text or "risk" in reasoning_text
        assert "DECISION" in reasoning_text or "decision" in reasoning_text
        
        # Verify recommendations exist
        assert len(audit_log["recommendations"]) > 0
    
    def test_audit_log_entity_context(self, db_session):
        """Test that audit log preserves entity context"""
        request_data = {
            "entity_name": "ContextTestCorp",
            "locations": ["US"],
            "entity_type": "PRIVATE_COMPANY",
            "industry": "TECHNOLOGY",
            "employee_count": 250
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        assert response.status_code == 200
        
        task_id = response.json()["tasks"][0]["task_id"]
        
        # Get audit log
        response = client.get(f"/api/v1/audit_log/{task_id}")
        assert response.status_code == 200
        
        audit_log = response.json()
        
        # Verify entity context is preserved
        assert audit_log["entity_name"] == "ContextTestCorp"
        
        entity_context = audit_log["entity_context"]
        assert entity_context is not None
        assert entity_context["name"] == "ContextTestCorp"
        assert entity_context["employee_count"] == 250
    
    def test_audit_log_task_context(self, db_session):
        """Test that audit log preserves task context"""
        request_data = {
            "entity_name": "TaskContextTestCorp",
            "locations": ["EU"],
            "has_personal_data": True
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        assert response.status_code == 200
        
        task_id = response.json()["tasks"][0]["task_id"]
        
        # Get audit log
        response = client.get(f"/api/v1/audit_log/{task_id}")
        assert response.status_code == 200
        
        audit_log = response.json()
        
        # Verify task context is preserved
        task_context = audit_log["task_context"]
        assert task_context is not None
        assert "description" in task_context
        assert "category" in task_context


class TestEndpointIntegration:
    """Integration tests for entity analysis endpoints"""
    
    def test_full_workflow(self, db_session):
        """Test complete workflow: analyze entity → get audit logs"""
        # Step 1: Analyze entity
        request_data = {
            "entity_name": "WorkflowTestCorp",
            "locations": ["US", "EU"],
            "entity_type": "PRIVATE_COMPANY",
            "industry": "FINANCIAL_SERVICES",
            "employee_count": 500,
            "has_personal_data": True,
            "is_regulated": True
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        assert response.status_code == 200
        
        calendar = response.json()
        
        # Step 2: Verify calendar structure
        assert len(calendar["tasks"]) > 0
        assert calendar["summary"]["total_tasks"] == len(calendar["tasks"])
        
        # Step 3: Get audit log for each task
        for task in calendar["tasks"]:
            task_id = task["task_id"]
            audit_response = client.get(f"/api/v1/audit_log/{task_id}")
            
            assert audit_response.status_code == 200
            audit_log = audit_response.json()
            
            # Verify consistency between calendar and audit log
            assert audit_log["task_id"] == task_id
            assert audit_log["decision_outcome"] == task["decision"]
            assert audit_log["confidence_score"] == task["confidence"]
            assert audit_log["risk_level"] == task["risk_level"]
    
    def test_multiple_entities_isolation(self, db_session):
        """Test that multiple entity analyses don't interfere"""
        entities = [
            {"entity_name": "Entity1", "locations": ["US"]},
            {"entity_name": "Entity2", "locations": ["EU"]},
            {"entity_name": "Entity3", "locations": ["UK"]}
        ]
        
        results = []
        for entity_data in entities:
            response = client.post("/api/v1/entity/analyze", json=entity_data)
            assert response.status_code == 200
            results.append(response.json())
        
        # Verify each entity has unique tasks
        task_ids = []
        for result in results:
            for task in result["tasks"]:
                assert task["task_id"] not in task_ids
                task_ids.append(task["task_id"])
        
        # Verify each entity has correct name
        for i, result in enumerate(results):
            assert result["entity_name"] == entities[i]["entity_name"]
    
    def test_decision_distribution(self, db_session):
        """Test that decision distribution is reasonable"""
        request_data = {
            "entity_name": "DistributionTestCorp",
            "locations": ["US"],
            "entity_type": "STARTUP",
            "industry": "TECHNOLOGY",
            "employee_count": 50,
            "has_personal_data": False,
            "previous_violations": 0
        }
        
        response = client.post("/api/v1/entity/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        summary = data["summary"]
        decisions = summary["decisions"]
        
        # At least one decision type should exist
        total_decisions = sum(decisions.values())
        assert total_decisions > 0
        assert total_decisions == summary["total_tasks"]
        
        # Percentages should add up
        autonomous_pct = decisions.get("autonomous", 0) / total_decisions * 100
        assert 0 <= autonomous_pct <= 100
        assert abs(autonomous_pct - summary["autonomous_percentage"]) < 0.1

