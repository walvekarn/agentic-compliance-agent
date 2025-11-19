"""Tests for the API routes"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, Mock, AsyncMock

from backend.main import app
from backend.db.base import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch('backend.api.routes.get_agent')
def test_process_query_endpoint(mock_get_agent):
    """Test the query processing endpoint"""
    # Create a mock agent instance
    mock_agent_instance = Mock()
    mock_agent_instance.process_query = AsyncMock(return_value={
        "status": "success",
        "response": "GDPR is a data protection regulation",
        "model": "gpt-4o-mini",
    })
    mock_get_agent.return_value = mock_agent_instance
    
    response = client.post(
        "/api/v1/query",
        json={"query": "What is GDPR?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "response" in data
    assert "query_id" in data


def test_create_rule_endpoint():
    """Test creating a compliance rule"""
    response = client.post(
        "/api/v1/rules",
        json={
            "title": "GDPR Article 5",
            "description": "Principles relating to processing of personal data",
            "category": "Data Protection",
            "regulation_source": "GDPR",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "GDPR Article 5"
    assert data["category"] == "Data Protection"
    assert "id" in data


def test_get_rules_endpoint():
    """Test getting list of rules"""
    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_rule_by_id_endpoint():
    """Test getting a specific rule"""
    # First create a rule
    create_response = client.post(
        "/api/v1/rules",
        json={
            "title": "HIPAA Security Rule",
            "description": "Protects health information",
            "category": "Healthcare",
        }
    )
    rule_id = create_response.json()["id"]
    
    # Then retrieve it
    response = client.get(f"/api/v1/rules/{rule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rule_id
    assert data["title"] == "HIPAA Security Rule"


def test_get_queries_endpoint():
    """Test getting list of queries"""
    response = client.get("/api/v1/queries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Cleanup
@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup test database after tests"""
    yield
    Base.metadata.drop_all(bind=engine)

