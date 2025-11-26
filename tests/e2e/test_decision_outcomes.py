"""
Reality-based decision outcome tests.

These are intended to catch regressions where the system returns
zero confidence or flattening of decision tiers across risk levels.

These tests use in-process TestClient and don't require an external server.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure we skip external server startup in conftest.py
os.environ["SKIP_LIVE_BACKEND"] = "1"

from backend.main import app
from backend.db.base import Base, get_db

# Test database (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_decision_outcomes.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def post_decision(payload: dict):
    response = client.post("/api/v1/decision/analyze", json=payload)
    return response


def assert_confidence_nonzero(body: dict, floor: float = 0.5):
    confidence = body.get("confidence") or body.get("confidence_score", 0)
    assert isinstance(confidence, (int, float)), "Confidence missing or not numeric"
    assert confidence >= floor, f"Confidence too low: {confidence}"
    return confidence


def test_medium_policy_review_is_get_approval():
    """Medium risk policy review should come back as REVIEW_REQUIRED with non-zero confidence."""
    payload = {
        "entity": {
            "name": "Acme Robotics",
            "entity_type": "PRIVATE_COMPANY",
            "industry": "TECHNOLOGY",
            "jurisdictions": ["US_FEDERAL", "EU"],
            "employee_count": 250,
            "has_personal_data": True,
            "is_regulated": False,
            "previous_violations": 0,
        },
        "task": {
            "description": "Update GDPR-compliant privacy policy for new personalization features.",
            "category": "POLICY_REVIEW",
            "affects_personal_data": True,
            "affects_financial_data": False,
            "involves_cross_border": True,
            "regulatory_deadline": None,
            "potential_impact": "Serious issues if wrong",
            "stakeholder_count": 50000,
        },
    }
    resp = post_decision(payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] in ["REVIEW_REQUIRED", "ESCALATE"], "Policy reviews should not be AUTONOMOUS"
    assert body["decision"] != "ESCALATE", "Privacy policy updates should not escalate by default"
    assert_confidence_nonzero(body, floor=0.65)
    assert body["risk_level"] in ["MEDIUM", "HIGH"]


def test_low_risk_internal_doc_can_be_autonomous():
    """Low-risk internal documentation changes should be autonomous with high confidence."""
    payload = {
        "entity": {
            "name": "Local Cafe Co",
            "entity_type": "PRIVATE_COMPANY",
            "industry": "RETAIL",
            "jurisdictions": ["US_FEDERAL"],
            "employee_count": 15,
            "has_personal_data": False,
            "is_regulated": False,
            "previous_violations": 0,
        },
        "task": {
            "description": "Update employee handbook vacation policy (no customer data).",
            "category": "GENERAL_INQUIRY",
            "affects_personal_data": False,
            "affects_financial_data": False,
            "involves_cross_border": False,
            "regulatory_deadline": None,
            "potential_impact": "Minor problems",
            "stakeholder_count": 15,
        },
    }
    resp = post_decision(payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] in ["AUTONOMOUS", "REVIEW_REQUIRED"], "Low-risk tasks must not escalate"
    assert body["decision"] == "AUTONOMOUS", f"Expected AUTONOMOUS for low-risk, got {body['decision']}"
    assert_confidence_nonzero(body, floor=0.75)
    assert body["risk_level"] in ["LOW", "MEDIUM"]


def test_high_risk_incident_escalates():
    """High-risk incident response should escalate with high confidence."""
    payload = {
        "entity": {
            "name": "Global Finance Corp",
            "entity_type": "PUBLIC_COMPANY",
            "industry": "FINANCIAL_SERVICES",
            "jurisdictions": ["US_FEDERAL", "EU", "UK"],
            "employee_count": 500,
            "has_personal_data": True,
            "is_regulated": True,
            "previous_violations": 1,
        },
        "task": {
            "description": "Incident response for data breach involving PII across EU and US.",
            "category": "INCIDENT_RESPONSE",
            "affects_personal_data": True,
            "affects_financial_data": True,
            "involves_cross_border": True,
            "regulatory_deadline": None,
            "potential_impact": "Major crisis with severe penalties",
            "stakeholder_count": 100000,
        },
    }
    resp = post_decision(payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "ESCALATE", f"High-risk incident must escalate, got {body['decision']}"
    assert_confidence_nonzero(body, floor=0.85)
    assert body["risk_level"] == "HIGH"
