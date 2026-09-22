"""Tests for the FastAPI routes.

The /api/v1 routes are JWT-protected, so a module fixture logs in with the
demo credentials (created by ensure_admin_user on first login) and every
protected request carries the resulting bearer token.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.db.base import Base, get_db
from backend.auth.user_manager import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

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


@pytest.fixture(scope="module")
def auth_headers():
    """Log in with the demo credentials and return a bearer-token header."""
    response = client.post(
        "/auth/login",
        data={"username": DEFAULT_ADMIN_USERNAME, "password": DEFAULT_ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


def test_login_returns_tokens():
    """The demo user can log in and receives access and refresh tokens."""
    response = client.post(
        "/auth/login",
        data={"username": DEFAULT_ADMIN_USERNAME, "password": DEFAULT_ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_protected_routes_require_auth():
    """Protected routes reject requests that carry no bearer token."""
    assert client.get("/api/v1/rules").status_code == 401
    assert client.get("/api/v1/queries").status_code == 401
    assert client.post("/api/v1/query", json={"query": "What is GDPR?"}).status_code == 401


@patch("backend.api.routes.get_agent")
def test_process_query_endpoint(mock_get_agent, auth_headers):
    """Test the query processing endpoint"""
    mock_agent_instance = Mock()
    mock_agent_instance.process_query = AsyncMock(return_value={
        "status": "success",
        "response": "GDPR is a data protection regulation",
        "model": "gpt-4o-mini",
    })
    mock_get_agent.return_value = mock_agent_instance

    response = client.post(
        "/api/v1/query",
        json={"query": "What is GDPR?"},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert data["response"] == "GDPR is a data protection regulation"
    assert data["query_id"] is not None
    mock_agent_instance.process_query.assert_awaited_once()


def test_create_rule_endpoint(auth_headers):
    """Test creating a compliance rule"""
    response = client.post(
        "/api/v1/rules",
        json={
            "title": "GDPR Article 5",
            "description": "Principles relating to processing of personal data",
            "category": "Data Protection",
            "regulation_source": "GDPR",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "GDPR Article 5"
    assert data["category"] == "Data Protection"
    assert "id" in data


def test_get_rules_endpoint(auth_headers):
    """Test getting list of rules"""
    response = client.get("/api/v1/rules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_rule_by_id_endpoint(auth_headers):
    """Test getting a specific rule"""
    create_response = client.post(
        "/api/v1/rules",
        json={
            "title": "HIPAA Security Rule",
            "description": "Protects health information",
            "category": "Healthcare",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200, create_response.text
    rule_id = create_response.json()["id"]

    response = client.get(f"/api/v1/rules/{rule_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rule_id
    assert data["title"] == "HIPAA Security Rule"


def test_get_rule_not_found(auth_headers):
    """An unknown rule id returns 404."""
    response = client.get("/api/v1/rules/999999", headers=auth_headers)
    assert response.status_code == 404


def test_get_queries_endpoint(auth_headers):
    """Test getting list of queries"""
    response = client.get("/api/v1/queries", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Cleanup
@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup test database after tests"""
    yield
    Base.metadata.drop_all(bind=engine)
